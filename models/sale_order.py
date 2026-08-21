# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    barca_project_id = fields.Many2one(
        "project.project",
        string="Proyecto",
        copy=False,
        ondelete="set null",
    )

    def action_confirm(self):
        self._sync_barca_project_customer_from_quote()
        result = super().action_confirm()
        self._adjudicar_barca_projects()
        return result

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders._sync_barca_project_customer_from_quote()
        return orders

    def write(self, vals):
        previous_states = {order.id: order.state for order in self}
        result = super().write(vals)
        if {"partner_id", "project_id", "state"} & set(vals):
            self._sync_barca_project_customer_from_quote()
        if vals.get("state") == "sale":
            confirmed_orders = self.filtered(
                lambda order: previous_states.get(order.id) != "sale"
            )
            confirmed_orders._adjudicar_barca_projects()
        return result

    def _sync_barca_project_customer_from_quote(self):
        if not self or "project_id" not in self._fields:
            return
        if not self._column_exists("project_id"):
            return
        orders = self.filtered(
            lambda order: order.state in ("draft", "sent")
            and order.project_id
            and order.partner_id
        )
        for order in orders.sudo():
            vals = {"partner_id": order.partner_id.id}
            if (
                order.project_id.establecimiento_id
                and order.project_id.establecimiento_id.parent_id != order.partner_id
            ):
                vals["establecimiento_id"] = False
            order.project_id.write(vals)

    def _adjudicar_barca_projects(self):
        if not self:
            return
        Project = self.env["project.project"].sudo()
        Project._ensure_barca_project_stages()
        licitacion_stage = Project._get_barca_project_stage("Licitacion")
        adjudicado_stage = Project._get_barca_project_stage("Adjudicado")
        if not adjudicado_stage:
            return
        projects = Project.browse()
        for field_name in self._get_barca_project_field_names():
            if field_name in self._fields:
                projects |= self.mapped(field_name).sudo()
        projects = projects.filtered(lambda project: "stage_id" in project._fields)
        if licitacion_stage:
            projects = projects.filtered(
                lambda project: project.stage_id == licitacion_stage or not project.stage_id
            )
        if not projects:
            return
        projects.write({"stage_id": adjudicado_stage.id})
        projects.filtered(lambda project: not project.fecha_adjudicacion).write(
            {"fecha_adjudicacion": fields.Date.context_today(self)}
        )

    def _get_barca_project_field_names(self):
        field_names = []
        for field_name in ("project_id", "project_ids", "barca_project_id"):
            field = self._fields.get(field_name)
            if not field:
                continue
            if field.store and field.type != "one2many" and not self._column_exists(field_name):
                continue
            field_names.append(field_name)
        return field_names

    def _column_exists(self, column_name):
        self.env.cr.execute(
            """
            SELECT 1
              FROM information_schema.columns
             WHERE table_name = 'sale_order'
               AND column_name = %s
            """,
            (column_name,),
        )
        return bool(self.env.cr.fetchone())
