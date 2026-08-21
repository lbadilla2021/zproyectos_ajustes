# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

PROJECT_STAGE_MODEL = "project.project.stage"


class ITTipoTrabajo(models.Model):
    _name = "it.tipo.trabajo"
    _description = "Tipo de Trabajo"

    name = fields.Char("Nombre", required=True)
    active = fields.Boolean(default=True)


class ITTipoServicio(models.Model):
    _name = "it.tipo.servicio"
    _description = "Tipo de Servicio"

    name = fields.Char("Nombre", required=True)
    active = fields.Boolean(default=True)


class ITEquipo(models.Model):
    _name = "it.equipo"
    _description = "Equipo"
    _order = "sequence, name"

    name = fields.Char("Nombre", required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)


class ProjectPersonaAsignada(models.Model):
    _name = "project.persona.asignada"
    _description = "Persona Asignada"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    project_id = fields.Many2one(
        "project.project",
        string="Proyecto",
        ondelete="cascade",
    )
    task_id = fields.Many2one("project.task", string="Tarea", ondelete="cascade")
    funcion_id = fields.Many2one("it.funcion", string="Funcion")
    allowed_employee_ids = fields.Many2many(
        "hr.employee",
        string="Empleados permitidos",
        related="funcion_id.employee_ids",
        readonly=True,
    )
    employee_id = fields.Many2one(
        "hr.employee",
        string="Nombre de la persona",
        domain="[('id', 'in', allowed_employee_ids)]",
    )
    tipo_jornada_id = fields.Many2one(
        "resource.calendar",
        string="Tipo de jornada",
        related="employee_id.resource_calendar_id",
        readonly=True,
    )
    ciudad_id = fields.Many2one(
        "hr.city",
        string="Ciudad",
        related="employee_id.city_id",
        readonly=True,
    )
    licencia = fields.Char("Licencia")
    equipo_id = fields.Many2one("it.equipo", string="Equipo")
    equipment_category_id = fields.Many2one(
        "maintenance.equipment.category",
        string="Categoría",
        ondelete="restrict",
    )
    vehicle_equipment_id = fields.Many2one(
        "maintenance.equipment",
        string="Vehículo",
        domain="[('category_id', '=', equipment_category_id), ('category_id', '!=', False)]",
        ondelete="restrict",
    )

    @api.onchange("funcion_id")
    def _onchange_funcion_id(self):
        for record in self:
            if record.employee_id not in record.allowed_employee_ids:
                record.employee_id = False

    @api.onchange("equipment_category_id")
    def _onchange_equipment_category_id(self):
        for record in self:
            if (
                record.vehicle_equipment_id
                and record.vehicle_equipment_id.category_id
                != record.equipment_category_id
            ):
                record.vehicle_equipment_id = False

    @api.constrains("equipment_category_id", "vehicle_equipment_id")
    def _check_vehicle_matches_equipment_category(self):
        for record in self.filtered("vehicle_equipment_id"):
            if not record.equipment_category_id:
                raise ValidationError(
                    _("Debe seleccionar una categoría antes del vehículo.")
                )
            if (
                record.vehicle_equipment_id.category_id
                != record.equipment_category_id
            ):
                raise ValidationError(
                    _(
                        "El vehículo seleccionado no pertenece a la categoría "
                        "de equipo indicada."
                    )
                )

    @api.constrains("funcion_id", "employee_id")
    def _check_employee_allowed_for_function(self):
        inactive_function = self.filtered(
            lambda line: line.funcion_id and not line.funcion_id.active
        )
        if inactive_function:
            raise ValidationError(
                _("No puede asignar una función que se encuentra desactivada.")
            )

        for record in self.filtered(lambda line: line.funcion_id and line.employee_id):
            if record.employee_id not in record.funcion_id.employee_ids:
                raise ValidationError(
                    _(
                        "El empleado %(employee)s no está habilitado para la función %(function)s."
                    )
                    % {
                        "employee": record.employee_id.name,
                        "function": record.funcion_id.name,
                    }
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            task_id = vals.get("task_id")
            if task_id and not vals.get("project_id"):
                vals["project_id"] = self.env["project.task"].browse(task_id).project_id.id
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("task_id") and not vals.get("project_id"):
            vals = dict(vals)
            vals["project_id"] = self.env["project.task"].browse(vals["task_id"]).project_id.id
        return super().write(vals)


class ProjectTask(models.Model):
    _inherit = "project.task"

    persona_asignada_line_ids = fields.One2many(
        "project.persona.asignada",
        "task_id",
        string="Personas Asignadas",
    )


class ProjectProject(models.Model):
    _inherit = "project.project"

    BARCA_PROJECT_STAGE_NAMES = [
        "Licitacion",
        "Perdido",
        "Adjudicado",
        "Planificado",
        "En Ejecución",
        "Por cobrar",
        "Facturado",
    ]
    BARCA_PROJECT_STAGE_XML_IDS = {
        "Licitacion": "zproyectos_ajustes.project_stage_licitacion",
        "Perdido": "zproyectos_ajustes.project_stage_perdido",
        "Adjudicado": "zproyectos_ajustes.project_stage_adjudicado",
        "Planificado": "zproyectos_ajustes.project_stage_planificado",
        "En Ejecución": "zproyectos_ajustes.project_stage_en_ejecucion",
        "Por cobrar": "zproyectos_ajustes.project_stage_por_cobrar",
        "Facturado": "zproyectos_ajustes.project_stage_facturado",
    }

    barca_codigo = fields.Char(
        "Codigo",
        copy=False,
        default=lambda self: _("Nuevo"),
        index=True,
    )
    numero_pedido = fields.Char("Número de Pedido / Orden de Servicio")
    ito = fields.Char("ITO")
    cliente_id = fields.Many2one(
        "res.partner",
        string="Cliente",
        related="partner_id",
        readonly=False,
        store=True,
        domain="[('parent_id', '=', False)]",
    )
    establecimiento_id = fields.Many2one(
        "res.partner",
        string="Establecimiento",
        domain="[('parent_id', '=', cliente_id)]",
    )
    descripcion_servicio = fields.Char(
        "Nombre de Servicio",
        related="name",
        readonly=False,
        store=True,
    )
    observacion = fields.Text("Observacion")
    tipo_trabajo_id = fields.Many2one("it.tipo.trabajo", string="Tipo de trabajo")
    tipo_servicio_id = fields.Many2one("it.tipo.servicio", string="Tipo de servicio")
    fecha_adjudicacion = fields.Date("Fecha Adjudicacion")
    fecha_inicio_programada = fields.Date(
        "Fecha Inicio Programada",
        related="date_start",
        readonly=False,
        store=True,
    )
    fecha_termino_programada = fields.Date(
        "Fecha Termino Programada",
        related="date",
        readonly=False,
        store=True,
    )
    duracion_horas = fields.Float("Duracion (horas)")
    cantidad_turnos = fields.Integer("Cantidad de turnos")
    cantidad_equipos = fields.Integer("Cantidad de equipos")
    valor_adjudicado = fields.Float("Valor Adjudicado")
    valor_final = fields.Float("Valor Final")
    barca_legacy_orden_servicio_id = fields.Integer(
        "ID Proyecto Barca anterior",
        copy=False,
        index=True,
    )

    @api.onchange("cliente_id")
    def _onchange_cliente_id(self):
        for record in self:
            if (
                record.establecimiento_id
                and record.establecimiento_id.parent_id != record.cliente_id
            ):
                record.establecimiento_id = False

    @api.constrains("name")
    def _check_nombre_servicio(self):
        for record in self:
            if not (record.name or "").strip():
                raise ValidationError(_("Debe ingresar el Nombre de Servicio."))

    @api.constrains("cliente_id", "establecimiento_id")
    def _check_establecimiento_cliente(self):
        for record in self.filtered("establecimiento_id"):
            if record.establecimiento_id.parent_id != record.cliente_id:
                raise ValidationError(
                    _("El establecimiento debe ser un contacto o direccion del cliente seleccionado.")
                )

    @api.model_create_multi
    def create(self, vals_list):
        default_stage = self._get_barca_project_stage("Licitacion")
        for vals in vals_list:
            if not vals.get("barca_codigo") or vals["barca_codigo"] == _("Nuevo"):
                vals["barca_codigo"] = (
                    self.env["ir.sequence"].next_by_code("it.proyecto") or _("Nuevo")
                )
            if default_stage and "stage_id" in self._fields and not vals.get("stage_id"):
                vals["stage_id"] = default_stage.id
        return super().create(vals_list)

    def write(self, vals):
        self._check_adjudicado_to_planificado_required_values(vals)
        return super().write(vals)

    def init(self):
        sequence = self.env["ir.sequence"].search([("code", "=", "it.proyecto")], limit=1)
        if not sequence:
            self.env["ir.sequence"].create(
                {
                    "name": "Proyecto Barca",
                    "code": "it.proyecto",
                    "prefix": "P",
                    "padding": 5,
                    "company_id": False,
                }
            )
        self._ensure_barca_project_stages()
        self._ensure_default_barca_project_stage()
        self._ensure_barca_codes()
        self._migrate_legacy_ordenes_servicio()

    def _get_project_stage_model(self):
        if PROJECT_STAGE_MODEL not in self.env:
            return False
        return self.env[PROJECT_STAGE_MODEL]

    def _ensure_barca_project_stages(self):
        Stage = self._get_project_stage_model()
        if Stage is False:
            return {}

        stages_by_name = {}
        for sequence, name in enumerate(self.BARCA_PROJECT_STAGE_NAMES, start=1):
            stage = Stage.with_context(active_test=False).search(
                [("name", "=", name)],
                limit=1,
            )
            if not stage:
                vals = {
                    "name": name,
                    "sequence": sequence * 10,
                }
                if "fold" in Stage._fields and name in ("Perdido", "Facturado"):
                    vals["fold"] = True
                stage = Stage.sudo().create(vals)
            elif "active" in Stage._fields and not stage.active:
                stage.sudo().active = True
            stages_by_name[name] = stage
        return stages_by_name

    @api.model
    def ensure_barca_project_stages(self):
        return self._ensure_barca_project_stages()

    def _get_barca_project_stage(self, name):
        Stage = self._get_project_stage_model()
        if Stage is False:
            return False
        stage = self.env.ref(
            self.BARCA_PROJECT_STAGE_XML_IDS.get(name, ""),
            raise_if_not_found=False,
        )
        if stage:
            return stage
        return Stage.with_context(active_test=False).search([("name", "=", name)], limit=1)

    def _check_adjudicado_to_planificado_required_values(self, vals):
        if "stage_id" not in vals:
            return

        planificado_stage = self._get_barca_project_stage("Planificado")
        if not planificado_stage or vals.get("stage_id") != planificado_stage.id:
            return

        adjudicado_stage = self._get_barca_project_stage("Adjudicado")
        for project in self:
            if adjudicado_stage and project.stage_id != adjudicado_stage:
                continue

            establecimiento_id = vals.get(
                "establecimiento_id",
                project.establecimiento_id.id,
            )
            numero_pedido = vals.get("numero_pedido", project.numero_pedido)
            missing_fields = []
            if not establecimiento_id:
                missing_fields.append(_("Establecimiento"))
            if not (numero_pedido or "").strip():
                missing_fields.append(_("Número de Pedido / Orden de Servicio"))

            if missing_fields:
                raise ValidationError(
                    _(
                        "Para cambiar el proyecto de Adjudicado a Planificado debe "
                        "completar: %s."
                    )
                    % ", ".join(missing_fields)
                )

    def _set_barca_project_stage(self, name):
        stage = self._get_barca_project_stage(name)
        if stage and "stage_id" in self._fields:
            self.write({"stage_id": stage.id})

    def _ensure_default_barca_project_stage(self):
        stage = self._get_barca_project_stage("Licitacion")
        if stage and "stage_id" in self._fields:
            self.search([("stage_id", "=", False)]).write({"stage_id": stage.id})

    @api.model
    def ensure_default_barca_project_stage(self):
        return self._ensure_default_barca_project_stage()

    def _ensure_barca_codes(self):
        for project in self.search([("barca_codigo", "=", False)]):
            project.barca_codigo = (
                self.env["ir.sequence"].next_by_code("it.proyecto") or _("Nuevo")
            )

    def _table_exists(self, table_name):
        self.env.cr.execute("SELECT to_regclass(%s)", (table_name,))
        return bool(self.env.cr.fetchone()[0])

    def _column_exists(self, table_name, column_name):
        self.env.cr.execute(
            """
            SELECT 1
              FROM information_schema.columns
             WHERE table_name = %s
               AND column_name = %s
            """,
            (table_name, column_name),
        )
        return bool(self.env.cr.fetchone())

    def _migrate_legacy_ordenes_servicio(self):
        if not self._table_exists("it_orden_servicio"):
            return

        stages_by_legacy_state = {
            "licitacion": self._get_barca_project_stage("Licitacion"),
            "perdido": self._get_barca_project_stage("Perdido"),
            "adjudicado": self._get_barca_project_stage("Adjudicado"),
            "planificado": self._get_barca_project_stage("Planificado"),
            "por_cobrar": self._get_barca_project_stage("Por cobrar"),
            "cobrado": self._get_barca_project_stage("Facturado"),
        }

        self.env.cr.execute(
            """
            SELECT id, name, numero_pedido, ito, cliente_id, establecimiento_id,
                   descripcion_servicio, observacion, tipo_trabajo_id, tipo_servicio_id,
                   fecha_adjudicacion, fecha_inicio_programada, fecha_termino_programada,
                   duracion_horas, cantidad_turnos, cantidad_equipos, valor_adjudicado,
                   valor_final, estado
              FROM it_orden_servicio
             ORDER BY id
            """
        )
        for legacy in self.env.cr.dictfetchall():
            project = self.search(
                [("barca_legacy_orden_servicio_id", "=", legacy["id"])],
                limit=1,
            )
            if project:
                continue
            vals = {
                "name": legacy["descripcion_servicio"] or legacy["name"],
                "barca_codigo": legacy["name"] or _("Nuevo"),
                "numero_pedido": legacy["numero_pedido"],
                "ito": legacy["ito"],
                "partner_id": legacy["cliente_id"],
                "establecimiento_id": legacy["establecimiento_id"],
                "observacion": legacy["observacion"],
                "tipo_trabajo_id": legacy["tipo_trabajo_id"],
                "tipo_servicio_id": legacy["tipo_servicio_id"],
                "fecha_adjudicacion": legacy["fecha_adjudicacion"],
                "fecha_inicio_programada": legacy["fecha_inicio_programada"],
                "fecha_termino_programada": legacy["fecha_termino_programada"],
                "duracion_horas": legacy["duracion_horas"],
                "cantidad_turnos": legacy["cantidad_turnos"],
                "cantidad_equipos": legacy["cantidad_equipos"],
                "valor_adjudicado": legacy["valor_adjudicado"],
                "valor_final": legacy["valor_final"],
                "barca_legacy_orden_servicio_id": legacy["id"],
            }
            stage = stages_by_legacy_state.get(legacy["estado"] or "licitacion")
            if stage and "stage_id" in self._fields:
                vals["stage_id"] = stage.id
            self.with_context(mail_create_nosubscribe=True).sudo().create(vals)

        if self._table_exists("it_informe") and self._column_exists("it_informe", "orden_servicio_id"):
            self.env.cr.execute(
                """
                UPDATE it_informe AS informe
                   SET orden_servicio_id = project.id
                  FROM project_project AS project
                 WHERE informe.orden_servicio_id = project.barca_legacy_orden_servicio_id
                   AND project.barca_legacy_orden_servicio_id IS NOT NULL
                """
            )

    def _sync_confirmed_sale_project_stages(self):
        if "sale.order" not in self.env:
            return
        confirmed_orders = self.env["sale.order"].sudo().search([("state", "=", "sale")])
        if confirmed_orders:
            confirmed_orders._adjudicar_barca_projects()
