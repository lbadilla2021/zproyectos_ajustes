# ZProyectos Ajustes

Extiende el modulo Proyectos de Odoo para incorporar la ficha Barca, sus etapas
operativas y su relacion con informes de turno.

## Responsabilidad

- Agrega la pestana **Proyecto Barca** al formulario de `project.project`.
- Usa `project.project.name` como Nombre de Servicio y conserva el codigo Barca
  en `barca_codigo`.
- Usa las fechas estandar del proyecto para Fecha Inicio Programada y Fecha
  Termino Programada.
- Asegura las etapas nativas de proyecto usadas por Barca: Licitacion, Perdido,
  Adjudicado, Planificado, En Ejecucion, Por cobrar y Facturado.
- Al confirmar un pedido de venta asociado a un proyecto, mueve el proyecto a
  la etapa Adjudicado.
- Expone los proyectos de Odoo a `zoperaciones_ajustes` para backend, website y
  PWA.
- Informe de Turno muestra proyectos en las etapas Adjudicado, Planificado y
  En Ejecucion.
- Incluye el mantenedor **Funciones operativas** para activar o desactivar las
  funciones disponibles.
- Filtra el empleado de **Personas Asignadas** segun la funcion elegida. Las
  funciones desactivadas permanecen visibles en el mantenedor, pero no se
  pueden seleccionar en una asignacion.
- Obtiene los empleados habilitados desde las funciones asignadas en la ficha
  del empleado por `zhr_ajustes`.
- Restringe la activacion y desactivacion de funciones al perfil **Gestionar
  asignaciones de funciones**.
# zproyectos_ajustes
# zproyectos_ajustes
