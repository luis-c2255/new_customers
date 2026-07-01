# 📊 Panel de control de análisis del sector minorista

Un panel de control interactivo creado con Streamlit para el análisis de clientes y ventas en el sector minorista —segmentación RFM, rendimiento de ventas y desgloses geográficos— diseñado para explorar el valor de los clientes y las tendencias comerciales de un solo vistazo.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B)
![Plotly](https://img.shields.io/badge/Plotly-charts-3F4F75)

## Características

- **KPI globales**: — ingresos, beneficios, margen, número de pedidos, valor medio por pedido y clientes activos, todos ellos adaptables a los filtros.
- **Segmentación de clientes RFM** — puntuación automática (reciencia, frecuencia, valor monetario) que clasifica a los clientes en segmentos VIP, en riesgo, nuevos, inactivos y habituales,  con un explorador de clientes por segmento en el que se pueden realizar búsquedas y descargar datos.
- **Rendimiento de ventas y productos** — tendencia mensual de ingresos y beneficios, un mapa de árbol con colores según los beneficios por categoría y subcategoría, y una clasificación de los 10 productos más vendidos.
- **Vista geográfica** — un mapa coroplético de EE. UU. y los 10 estados con mayores ingresos, con normalización automática de los nombres de las ciudades (p. ej., Chicago, Houston) según su estado.
- **Filtros globales** — género, categoría de producto, segmento de negocio y rango de fechas, todos ellos aplicados de forma coherente en todas las pestañas.
- **Exportación a CSV** — descarga cualquier lista de segmentos de clientes directamente desde la aplicación.

## Estructura del proyecto

```
.
├── app.py                # Aplicación Streamlit
├── customer_data.csv     # Datos demográficos y de perfil de los clientes
├── order_data.csv        # Datos de pedidos y transacciones
└── README.md
```

## Primeros pasos

### Requisitos previos

- Python 3.9+
- `customer_data.csv` y `order_data.csv` deben estar en la misma carpeta que `app.py`

### Instalación

```bash
pip install streamlit pandas plotly
```

### Ejecutar la aplicación

```bash
streamlit run app.py
```

La aplicación se abrirá automáticamente en `http://localhost:8501`.

## Datos

El panel de control une dos conjuntos de datos por el `Customer ID`:

**`customer_data.csv`** — una fila por cliente
| Columna | Descripción |
|---|---|
| `Customer ID` | Identificador único del cliente |
| `Age`, `Gender` | Datos Demográficos |
| `Location` | Estado de EE. UU. (o un pequeño número de ciudades importantes, normalizadas en la aplicación) |
| `Purchase Amount (USD)`, `Previous Purchases` | Datos históricos de compra |
| `Subscription Status`, `Discount Applied`, `Payment Method`, `Frequency of Purchases` | Atributos de comportamiento |

**`order_data.csv`** — una fila por línea de pedido
| Columna | Descripción |
|---|---|
| `Order Id`, `Order Date`, `Customer ID` | Identificadores del pedido |
| `Ship Mode`, `Segment`, `Category`, `Sub Category`, `Product Id` | Atributos del pedido |
| `cost price`, `List Price`, `Quantity`, `Discount Percent` | Se utilizan para calcular los ingresos, el coste y el beneficio |

`Total_Sales`, `Total_Cost`, and `Profit` son columnas derivadas que se calculan en el momento de la carga.

### Metodología RFM

A cada cliente se le asigna una puntuación del 1 al 4 (siendo 4 la mejor) en tres dimensiones, utilizando cuartiles basados en la clasificación para evitar errores derivados de valores duplicados:

- **Recencia (R)** — dias transcurridos desde el último pedido del cliente
- **Frecuencia (F)** — número total de pedidos realizados
- **Valor Monetario (M)** — importe total gastado

Las puntuaciones se agrupan en cinco segmentos:

| Segmento | Lógica |
|---|---|
| 🏆 Campeones (VIP) | R ≥ 3, F ≥ 3, M ≥ 3 |
| ⚠️ En Riesgo de Abandono | R ≤ 2, F ≥ 3, M ≥ 3 |
| 🌱 Nuevos Clientes | R ≥ 3, F ≤ 2 |
| 💤 Clientes Dormidos | R ≤ 2, F ≤ 2 |
| Clientes Regulares | Everything else |

## Especificaciones técnicas

- [Streamlit](https://streamlit.io/) — marco de trabajo de la aplicación e interfaz de usuario
- [Pandas](https://pandas.pydata.org/) — procesamiento de datos
- [Plotly Express](https://plotly.com/python/plotly-express/) —  gráficos interactivos

## Notas y limitaciones

- Algunas filas de la columna `Location` corresponden a ciudades en lugar de estados; estas se asignan a su estado correspondiente para la vista geográfica. Cualquier ubicación que no se pueda resolver queda excluida del mapa y se señala con una advertencia en la aplicación.
- Los clientes sin pedidos que coincidan (o viceversa) se descartan mediante la unión interna, ya que las métricas RFM y de ventas requieren tanto datos de compra como de perfil.

## Licencia

Este proyecto se proporciona «tal cual» con fines de cartera y educativos.
