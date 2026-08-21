from ast import literal_eval

from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase
from lxml import etree


class TestFunctionAssignment(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.function = cls.env.ref("zhr_ajustes.it_funcion_lavador_1")
        cls.allowed_employee = cls.env["hr.employee"].create(
            {"name": "Lavador habilitado"}
        )
        cls.other_employee = cls.env["hr.employee"].create(
            {"name": "Empleado no habilitado"}
        )
        cls.allowed_employee.funcion_ids = [Command.set(cls.function.ids)]
        cls.vehicle_category = cls.env[
            "maintenance.equipment.category"
        ].create({"name": "Camionetas de prueba"})
        cls.other_vehicle_category = cls.env[
            "maintenance.equipment.category"
        ].create({"name": "Bombas de prueba"})
        cls.vehicle = cls.env["maintenance.equipment"].create(
            {
                "name": "Vehiculo de prueba",
                "category_id": cls.vehicle_category.id,
            }
        )
        cls.other_vehicle = cls.env["maintenance.equipment"].create(
            {
                "name": "Otro vehiculo de prueba",
                "category_id": cls.other_vehicle_category.id,
            }
        )

        cls.assignment_manager = cls.env["res.users"].create(
            {
                "name": "Responsable asignaciones",
                "login": "responsable.asignaciones@example.com",
                "groups_id": [
                    Command.set(
                        cls.env.ref(
                            "zhr_ajustes.group_zhr_function_manager"
                        ).ids
                    )
                ],
            }
        )
        cls.project_user = cls.env["res.users"].create(
            {
                "name": "Usuario normal de proyecto",
                "login": "usuario.normal.proyecto@example.com",
                "groups_id": [
                    Command.set(cls.env.ref("project.group_project_user").ids)
                ],
            }
        )

    def test_function_maintainer_is_no_longer_owned_by_projects(self):
        self.assertFalse(
            self.env.ref(
                "zproyectos_ajustes.group_project_function_assignment_manager",
                raise_if_not_found=False,
            )
        )
        self.assertFalse(
            self.env.ref(
                "zproyectos_ajustes.menu_it_funcion",
                raise_if_not_found=False,
            )
        )

    def test_employee_must_be_enabled_for_function(self):
        assignment = self.env["project.persona.asignada"].create(
            {
                "funcion_id": self.function.id,
                "employee_id": self.allowed_employee.id,
            }
        )
        self.assertEqual(assignment.employee_id, self.allowed_employee)

        with self.assertRaises(ValidationError):
            self.env["project.persona.asignada"].create(
                {
                    "funcion_id": self.function.id,
                    "employee_id": self.other_employee.id,
                }
            )

    def test_vehicle_must_match_selected_equipment_category(self):
        assignment = self.env["project.persona.asignada"].create(
            {
                "equipment_category_id": self.vehicle_category.id,
                "vehicle_equipment_id": self.vehicle.id,
            }
        )
        self.assertEqual(assignment.vehicle_equipment_id, self.vehicle)

        with self.assertRaises(ValidationError):
            self.env["project.persona.asignada"].create(
                {
                    "equipment_category_id": self.vehicle_category.id,
                    "vehicle_equipment_id": self.other_vehicle.id,
                }
            )

    def test_changing_category_clears_an_incompatible_vehicle(self):
        assignment = self.env["project.persona.asignada"].new(
            {
                "equipment_category_id": self.vehicle_category.id,
                "vehicle_equipment_id": self.vehicle.id,
            }
        )
        assignment.equipment_category_id = self.other_vehicle_category
        assignment._onchange_equipment_category_id()
        self.assertFalse(assignment.vehicle_equipment_id)

    def test_personas_asignadas_view_replaces_camioneta_and_bomba(self):
        arch = self.env["project.task"].get_view(view_type="form")["arch"]
        xml = etree.fromstring(arch)
        self.assertFalse(xml.xpath("//field[@name='camioneta']"))
        self.assertFalse(xml.xpath("//field[@name='bomba']"))
        category_fields = xml.xpath("//field[@name='equipment_category_id']")
        vehicle_fields = xml.xpath("//field[@name='vehicle_equipment_id']")
        self.assertTrue(category_fields)
        self.assertTrue(vehicle_fields)
        self.assertEqual(
            vehicle_fields[0].get("domain"),
            "[('category_id', '=', equipment_category_id), ('category_id', '!=', False)]",
        )
        self.assertEqual(
            vehicle_fields[0].get("readonly"),
            "not equipment_category_id",
        )

    def test_employee_selector_does_not_allow_creation_or_opening(self):
        arch = self.env["project.task"].get_view(view_type="form")["arch"]
        employee_fields = etree.fromstring(arch).xpath(
            "//field[@name='persona_asignada_line_ids']"
            "//field[@name='employee_id']"
        )
        self.assertTrue(employee_fields)
        options = literal_eval(employee_fields[0].get("options"))
        self.assertTrue(options["no_create"])
        self.assertTrue(options["no_quick_create"])
        self.assertTrue(options["no_create_edit"])
        self.assertTrue(options["no_open"])

    def test_project_user_cannot_modify_function_maintainer(self):
        with self.assertRaises(AccessError):
            self.function.with_user(self.project_user).write({"active": False})

        with self.assertRaises(AccessError):
            self.function.with_user(self.project_user).action_archive()

        with self.assertRaises(AccessError):
            self.function.with_user(self.project_user).toggle_active()

    def test_assignment_profile_can_change_active(self):
        self.function.with_user(self.assignment_manager).action_archive()
        self.assertFalse(self.function.active)

        self.function.with_user(self.assignment_manager).action_unarchive()
        self.assertTrue(self.function.active)

        with self.assertRaises(AccessError):
            self.function.with_user(self.assignment_manager).write(
                {"name": "Cambio no permitido"}
            )

    def test_deactivate_archives_instead_of_deleting(self):
        function_id = self.function.id
        self.function.with_user(self.assignment_manager).active = False

        self.assertFalse(self.env["it.funcion"].search([("id", "=", function_id)]))
        archived = self.env["it.funcion"].with_context(active_test=False).browse(function_id)
        self.assertTrue(archived.exists())
        self.assertFalse(archived.active)

        action = self.env.ref("zhr_ajustes.action_it_funcion")
        self.assertIn("'active_test': False", action.context)

        with self.assertRaises(ValidationError):
            self.env["project.persona.asignada"].create(
                {
                    "funcion_id": archived.id,
                    "employee_id": self.allowed_employee.id,
                }
            )
