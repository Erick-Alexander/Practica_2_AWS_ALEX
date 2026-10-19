"""
PRÁCTICA 2: GENERACIÓN Y ESTRUCTURACIÓN DE UN ESQUEMA ESTRELLA.
Descripción:
    Script de ETL en Python (Pandas/Numpy) que transforma datos transaccionales 
    operacionales (OLTP) en un modelo multidimensional (Esquema Estrella / OLAP).
    
    Genera tablas de dimensión (Dim_Cliente, Dim_Producto, Dim_Tiempo) con 
    Surrogate Keys (SK) y una tabla de hechos (Fact_Ventas) con métricas avanzadas.

Autores/Integrantes: ALCYB Studios osea el Alex
Entorno: Python 3.10+ | Pandas | Numpy | PostgreSQL (EC2 AWS)
"""

import pandas as pd
import numpy as np

def ejecutar_pipeline_etl():
    # Desde aquí se simulan los datos reales de los operativos, desde la semilla 101.
    np.random.seed(101)
    n = 500
    
    df_operativo = pd.DataFrame({
        'id_transaccion': range(1000, 1000 + n),
        'fecha_hora': pd.date_range(start='2026-01-01', periods=n, freq='h'),
        'cliente_nombre': np.random.choice(['Juan Pérez', 'María Gómez', 'Carlos Ruiz', 'Ana López'], n),
        'cliente_ciudad': np.random.choice(['Puebla', 'CDMX', 'Guadalajara', 'Monterrey'], n),
        'producto_nombre': np.random.choice(['Laptop Dell', 'Mouse Logi', 'Monitor LG', 'Teclado Redragon'], n),
        'categoria_prod': np.random.choice(['Cómputo', 'Accesorios', 'Pantallas'], n),
        'precio_unitario': np.random.choice([15000.0, 350.0, 4500.0, 850.0], n),
        'cantidad': np.random.randint(1, 5, n)
    })

    # Desde aquí se delimitan los datos del cliente.
    dim_cliente = df_operativo[['cliente_nombre', 'cliente_ciudad']].drop_duplicates().reset_index(drop=True)
    dim_cliente['id_cliente_sk'] = dim_cliente.index + 1
    dim_cliente = dim_cliente[['id_cliente_sk', 'cliente_nombre', 'cliente_ciudad']]

    # Desde aquí se delimitan los datos del producto.
    dim_producto = df_operativo[['producto_nombre', 'categoria_prod', 'precio_unitario']].drop_duplicates().reset_index(drop=True)
    dim_producto['id_producto_sk'] = dim_producto.index + 1
    dim_producto = dim_producto[['id_producto_sk', 'producto_nombre', 'categoria_prod', 'precio_unitario']]

    # Desde aquí se delimitan los datos del tiempo.
    dim_tiempo = pd.DataFrame({'fecha_completa': df_operativo['fecha_hora'].dt.date.unique()})
    dim_tiempo['fecha_completa'] = pd.to_datetime(dim_tiempo['fecha_completa'])
    dim_tiempo['id_tiempo_sk'] = dim_tiempo['fecha_completa'].dt.strftime('%Y%m%d').astype(int)
    dim_tiempo['anio'] = dim_tiempo['fecha_completa'].dt.year
    dim_tiempo['mes'] = dim_tiempo['fecha_completa'].dt.month
    dim_tiempo['dia'] = dim_tiempo['fecha_completa'].dt.day
    
    dias_espanol = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
    dim_tiempo['dia_semana'] = dim_tiempo['fecha_completa'].dt.dayofweek
    dim_tiempo['nombre_dia'] = dim_tiempo['dia_semana'].map(dias_espanol)
    dim_tiempo['es_fin_semana'] = dim_tiempo['dia_semana'].isin([5, 6]).astype(int)
    dim_tiempo = dim_tiempo[['id_tiempo_sk', 'fecha_completa', 'anio', 'mes', 'dia', 'dia_semana', 'nombre_dia', 'es_fin_semana']]

    # Desde aquí se delimitan los datos de las facturas de ventas.
    fact_ventas = df_operativo.merge(dim_cliente, on=['cliente_nombre', 'cliente_ciudad'])\
                              .merge(dim_producto, on=['producto_nombre', 'categoria_prod', 'precio_unitario'])
    fact_ventas['fecha_completa'] = pd.to_datetime(fact_ventas['fecha_hora'].dt.date)
    fact_ventas = fact_ventas.merge(dim_tiempo, on='fecha_completa')

    # Desde aquí se calculan las métricas.
    fact_ventas['monto_bruto'] = fact_ventas['cantidad'] * fact_ventas['precio_unitario']
    fact_ventas['monto_descuento'] = np.where(fact_ventas['cantidad'] >= 3, fact_ventas['monto_bruto'] * 0.10, 0.0)
    monto_subtotal = fact_ventas['monto_bruto'] - fact_ventas['monto_descuento']
    fact_ventas['impuesto_iva'] = monto_subtotal * 0.16
    fact_ventas['monto_neto'] = monto_subtotal + fact_ventas['impuesto_iva']

    fact_table = fact_ventas[[
        'id_transaccion', 'id_cliente_sk', 'id_producto_sk', 'id_tiempo_sk',
        'cantidad', 'precio_unitario', 'monto_bruto', 'monto_descuento', 'impuesto_iva', 'monto_neto'
    ]]

    return dim_cliente, dim_producto, dim_tiempo, fact_table

if __name__ == "__main__":
    ejecutar_pipeline_etl()
