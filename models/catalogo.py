from models.db import ConexionBD

class Catalogo:
    @staticmethod
    def obtener_disponibles():
        return Catalogo.__consultar_base_catalogo(solo_disponibles=True)

    @staticmethod
    def obtener_por_placa(placa):
        res = Catalogo.__consultar_base_catalogo(placa=placa)
        return res[0] if res else None

    @staticmethod
    def __consultar_base_catalogo(solo_disponibles=False, placa=None):
        """
        MÉTODO ACTUALIZADO: Usa el Procedimiento Almacenado sp_obtener_catalogo_detallado
        y agrupa las múltiples imágenes por vehículo.
        """
        conexion = ConexionBD.obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        
        try:
            parametros = (placa, solo_disponibles)
            cursor.callproc('sp_obtener_catalogo_detallado', parametros)
            
            resultados = []
            for result in cursor.stored_results():
                resultados = result.fetchall()
            
            # Agrupar por vehículo para evitar filas duplicadas por cada foto
            catalogo_dict = {}
            for item in resultados:
                p = item['placa']
                if p not in catalogo_dict:
                    elem = dict(item)
                    elem['precio'] = float(elem['precio']) if elem.get('precio') else 0.0
                    elem['imagenes_lista'] = []
                    
                    foto = item.get('imagen_url') or item.get('URL')
                    if foto:
                        elem['imagenes_lista'].append(foto)
                        
                    catalogo_dict[p] = elem
                else:
                    foto = item.get('imagen_url') or item.get('URL')
                    if foto and foto not in catalogo_dict[p]['imagenes_lista']:
                        catalogo_dict[p]['imagenes_lista'].append(foto)

            # Asignar la primera imagen como foto de portada
            for v in catalogo_dict.values():
                v['imagen_url'] = v['imagenes_lista'][0] if v['imagenes_lista'] else None

            return list(catalogo_dict.values())
        except Exception as e:
            print(f"Error en procedimiento catálogo: {e}")
            return []
        finally:
            cursor.close()
            conexion.close()