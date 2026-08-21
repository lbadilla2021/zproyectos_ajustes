# -*- coding: utf-8 -*-


def sync_confirmed_sale_project_stages(env):
    env["project.project"].sudo()._sync_confirmed_sale_project_stages()
