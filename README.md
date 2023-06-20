# Explorador de facturas y declaraciones mensuales del SAT
Esta herramienta es un visor web que permite cargar información de facturas XML y declaraciones mensuales en PDF para ayudar a llevar un registro de la contabilidad ante el SAT (recaudador de impuestos en México).

La herramienta ofrece 4 funciones:
- **Cargar facturas**: permite seleccionar los archivos XML de facturas de ingresos o gastos que se quieren guardar en la base de datos.
- **Ver facturas**: permite ver las facturas cargadas previamente para un mes de un ejercicio fiscal. También provee algunos cálculos para ayudar a llenar la declaración mensual de impuestos.
- **Cargar declaraciones**: permite seleccionar los archivos PDF de la declaración mensual de la plataforma del SAT que se quieren guardar en la base de datos.
- **Ver declaraciones**: permite ver las declaraciones cargadas previamente para un ejercicio fiscal.

## Ejecución
Es necsario tener instalado Python 3.10 e instalar las librerías que están en el archivo `requirements.txt`.
Se debe crear un archivo `.env` con las siguientes variables:
```bash
CLIENT_RFC=XXXXXXXXXXXXX
DATABASE_FILE="app/data/contabilidad_sat.sqlite"
```

