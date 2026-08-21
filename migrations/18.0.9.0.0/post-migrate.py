from odoo import Command, SUPERUSER_ID, api


def _xml_record(env, module, name):
    xml_data = env['ir.model.data'].search(
        [('module', '=', module), ('name', '=', name)],
        limit=1,
    )
    if not xml_data:
        return xml_data, False
    return xml_data, env[xml_data.model].browse(xml_data.res_id).exists()


def _remove_xml_record(env, module, name):
    xml_data, record = _xml_record(env, module, name)
    if record:
        record.unlink()
    if xml_data.exists():
        xml_data.unlink()


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    legacy_xml_data, legacy_group = _xml_record(
        env,
        'zproyectos_ajustes',
        'group_project_function_assignment_manager',
    )
    new_group = env.ref(
        'zhr_ajustes.group_zhr_function_manager',
        raise_if_not_found=False,
    )
    if legacy_group and new_group:
        new_group.write(
            {'users': [Command.link(user.id) for user in legacy_group.users]}
        )

    for xml_name in (
        'menu_it_funcion',
        'action_it_funcion',
        'view_it_funcion_list',
        'view_it_funcion_form',
        'view_it_funcion_search',
    ):
        _remove_xml_record(env, 'zproyectos_ajustes', xml_name)

    if legacy_group:
        env['ir.model.access'].search(
            [('group_id', '=', legacy_group.id)]
        ).unlink()
        legacy_group.unlink()
    if legacy_xml_data.exists():
        legacy_xml_data.unlink()

    for xml_name in (
        'module_category_zproyectos_function_assignment',
        'module_category_zproyectos_ajustes',
    ):
        _remove_xml_record(env, 'zproyectos_ajustes', xml_name)
