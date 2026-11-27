import unittest
from unittest.mock import MagicMock, patch

from models.insumo import Insumo


class TestInsumo(unittest.TestCase):

    def setUp(self):
        self.conexion = MagicMock()
        self.cursor = MagicMock()
        self.conexion.cursor.return_value = self.cursor

        self.patch_conexion = patch(
            "models.insumo.ConexionBD.obtener_conexion",
            return_value=self.conexion
        )
        self.patch_conexion.start()
        self.addCleanup(self.patch_conexion.stop)

    def test_inicializar_insumo_con_todos_los_datos(self):
        insumo = Insumo("Aceite", "Aceite para mantenimiento", 15)
        self.assertEqual(insumo.nombre_insumo, "Aceite")
        self.assertEqual(insumo.descripcion, "Aceite para mantenimiento")
        self.assertEqual(insumo.stock, 15)

    def test_inicializar_insumo_con_valores_predeterminados(self):
        insumo = Insumo("Filtro")
        self.assertEqual(insumo.nombre_insumo, "Filtro")
        self.assertIsNone(insumo.descripcion)
        self.assertEqual(insumo.stock, 0)

    def test_obtener_todos_devuelve_lista_de_insumos(self):
        datos = [
            {"cod_insumo": 1, "nombre_insumo": "Aceite", "stock": 10},
            {"cod_insumo": 2, "nombre_insumo": "Filtro", "stock": 5},
        ]
        self.cursor.fetchall.return_value = datos

        resultado = Insumo.obtener_todos()

        self.conexion.cursor.assert_called_once_with(dictionary=True)
        self.cursor.execute.assert_called_once_with(
            "SELECT * FROM insumos ORDER BY nombre_insumo"
        )
        self.assertEqual(resultado, datos)
        self.cursor.close.assert_called_once()
        self.conexion.close.assert_called_once()

    def test_obtener_todos_devuelve_lista_vacia_cuando_no_hay_registros(self):
        self.cursor.fetchall.return_value = []
        resultado = Insumo.obtener_todos()
        self.assertEqual(resultado, [])
        self.cursor.close.assert_called_once()
        self.conexion.close.assert_called_once()

    def test_obtener_por_id_devuelve_el_insumo(self):
        dato = {
            "cod_insumo": 3,
            "nombre_insumo": "Bujía",
            "descripcion": "Bujía de vehículo",
            "stock": 8,
        }
        self.cursor.fetchone.return_value = dato

        resultado = Insumo.obtener_por_id(3)

        self.cursor.execute.assert_called_once_with(
            "SELECT * FROM insumos WHERE cod_insumo = %s", (3,)
        )
        self.assertEqual(resultado, dato)
        self.cursor.close.assert_called_once()
        self.conexion.close.assert_called_once()

    def test_obtener_por_id_devuelve_none_si_no_existe(self):
        self.cursor.fetchone.return_value = None
        resultado = Insumo.obtener_por_id(999)
        self.assertIsNone(resultado)
        self.cursor.close.assert_called_once()
        self.conexion.close.assert_called_once()

    def test_crear_insumo_guarda_y_devuelve_codigo_generado(self):
        self.cursor.lastrowid = 12

        resultado = Insumo.crear(
            "Pastillas de freno", "Repuesto para sistema de frenos", 20
        )

        consulta, parametros = self.cursor.execute.call_args[0]
        self.assertIn("INSERT INTO insumos", consulta)
        self.assertEqual(
            parametros,
            ("Pastillas de freno", "Repuesto para sistema de frenos", 20),
        )
        self.conexion.commit.assert_called_once()
        self.assertEqual(resultado, 12)
        self.cursor.close.assert_called_once()
        self.conexion.close.assert_called_once()

    def test_crear_insumo_usa_stock_cero_por_defecto(self):
        self.cursor.lastrowid = 13
        resultado = Insumo.crear("Filtro de aire", "Filtro")

        parametros = self.cursor.execute.call_args[0][1]
        self.assertEqual(parametros, ("Filtro de aire", "Filtro", 0))
        self.assertEqual(resultado, 13)
        self.conexion.commit.assert_called_once()

    def test_actualizar_insumo_ejecuta_update_y_confirma(self):
        resultado = Insumo.actualizar(
            4, "Aceite sintético", "Aceite 5W-30", 25
        )

        consulta, parametros = self.cursor.execute.call_args[0]
        self.assertIn("UPDATE insumos", consulta)
        self.assertEqual(
            parametros, ("Aceite sintético", "Aceite 5W-30", 25, 4)
        )
        self.conexion.commit.assert_called_once()
        self.assertTrue(resultado)
        self.cursor.close.assert_called_once()
        self.conexion.close.assert_called_once()

    def test_eliminar_insumo_ejecuta_delete_y_confirma(self):
        resultado = Insumo.eliminar(6)

        consulta, parametros = self.cursor.execute.call_args[0]
        self.assertIn("DELETE FROM insumos", consulta)
        self.assertEqual(parametros, (6,))
        self.conexion.commit.assert_called_once()
        self.assertTrue(resultado)
        self.cursor.close.assert_called_once()
        self.conexion.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
