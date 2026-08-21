# -*- coding: utf-8 -*-
{
    "name": "Barca Ajustes al modulo Proyectos",
    "summary": "Integra la ficha Barca dentro de Proyectos de Odoo",
    "version": "18.0.9.1.0",
    "category": "Project",
    "author": "ZOC",
    "license": "LGPL-3",
    "depends": [
        "project",
        "maintenance",
        "hr",
        "zhr_ajustes",
        "sale",
        "sale_project",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/project_stage_data.xml",
        "data/equipo_data.xml",
        "views/tipo_trabajo_servicio_views.xml",
        "views/sale_order_views.xml",
        "views/project_project_views.xml",
        "views/project_task_views.xml",
    ],
    "installable": True,
    "application": False,
    "post_init_hook": "sync_confirmed_sale_project_stages",
}
