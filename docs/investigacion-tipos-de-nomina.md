# Investigación: tipos de nómina en México

Fase 1 del plan. Solo investigación: no cambia código.
Fecha: 24-09-2026.

**Cómo leer este documento**

- ✔ = dato confirmado en una fuente oficial (DOF, SAT, texto de la ley). La fuente está en la sección 9.
- ⚠ SIN VERIFICAR = sale de fuentes secundarias o de conocimiento general. Hay que confirmarlo antes de programarlo.

**Decisiones tomadas (24-09-2026)**

- MVP aprobado: `02 Sueldos` + `09 Asimilados honorarios`.
- Las empresas operan principalmente en **San Luis Potosí** (ISN en la sección 4.1).
- Las correcciones del cálculo actual (sección 7.3) van en una fase aparte.

---

## 0. Resumen

1. **"RESICO asalariado" no es un tipo de nómina.** RESICO es un régimen *del trabajador* para lo que cobra por su cuenta. Si además tiene un sueldo, el patrón calcula su nómina **exactamente igual** que la de cualquier asalariado. Que esté en RESICO no cambia nada del recibo.
2. **Lo que cambia el cálculo es el "tipo de régimen" de la nómina** (catálogo `c_TipoRegimen` del SAT: 02 Sueldos, 09 Asimilados honorarios, 13 Indemnización, etc.). No es el régimen fiscal del trabajador.
3. **Asimilados a salarios** (honorarios asimilados) usan la misma tabla de ISR, pero sin IMSS, sin INFONAVIT, sin subsidio para el empleo y sin las exenciones de aguinaldo y prima vacacional.
4. **Dato importante:** quien cobra como asimilado por honorarios, consejero o actividades empresariales asimiladas **no puede estar en RESICO**. Un asalariado normal **sí puede**.
5. **Recomendación para ya (MVP):** agregar al empleado un campo "tipo de régimen" con dos opciones: `02 Sueldos` (lo que CEN ya hace) y `09 Asimilados honorarios`.
6. **Los valores 2026 del código ya coinciden** con las fuentes oficiales: tabla de ISR, UMA y límite del subsidio. Solo el monto del subsidio tiene una diferencia de centavos (ver 7.3).

---

## 1. Dos conceptos que se confunden

| Concepto | Qué es | Ejemplos | ¿Cambia el cálculo de la nómina? |
|---|---|---|---|
| **Régimen fiscal del trabajador** (`c_RegimenFiscal`) | En qué régimen está inscrito el trabajador en el SAT (aparece en su constancia de situación fiscal) | 605 Sueldos y salarios, 626 RESICO, 612 Actividad empresarial | **No** |
| **Tipo de régimen de la nómina** (`c_TipoRegimen`) | Bajo qué figura le paga el patrón | 02 Sueldos, 09 Asimilados honorarios, 13 Indemnización | **Sí** |

En el CFDI de nómina, el régimen fiscal del receptor **siempre** es `605` ✔:

> Guía SAT: se debe registrar la clave "605" Sueldos y Salarios e Ingresos Asimilados a Salarios como régimen fiscal del receptor (trabajador asalariado o asimilado a salarios).

La misma guía pide que el trabajador tenga ese régimen dado de alta en el SAT "para evitar problemas" al emitir el comprobante ✔.

---

## 2. Respuesta directa: alguien en RESICO que también es asalariado

**¿Puede estar en RESICO y cobrar un sueldo?** ✔ Sí. El art. 113-E LISR permite tributar en RESICO aunque también se tengan ingresos de sueldos y salarios (Capítulo I) o intereses (Capítulo VI). La condición es que el total de ingresos del año anterior no pase de **$3,500,000**.

**Excepción importante** ✔ (art. 113-E, fracción IV). **No** pueden estar en RESICO quienes cobren ingresos asimilados de las fracciones III, IV, V o VI del art. 94:

- consejeros, administradores, comisarios y gerentes generales (fr. III)
- honorarios cobrados principalmente a un solo prestatario, en sus instalaciones (fr. IV)
- honorarios con opción por escrito de tributar como asimilado (fr. V)
- actividades empresariales con opción por escrito de tributar como asimilado (fr. VI)

Es decir: **asalariado + RESICO sí; asimilado por honorarios + RESICO no.**

**¿Qué hace el patrón en la nómina?** Nada distinto:

- Tipo de régimen `02 Sueldos`, ISR con la tabla del art. 96, cuota obrera del IMSS y subsidio para el empleo si le toca.
- El recibo es igual al de cualquier trabajador.
- En el CFDI: receptor con régimen `605`.

**¿Y si en el SAT solo tiene el régimen 626 (RESICO)?** La guía pide que el trabajador esté en el 605 ✔. Tendría que agregar la obligación de sueldos y salarios en el SAT antes de que se le timbre su nómina.
⚠ SIN VERIFICAR: si el PAC rechaza el timbrado cuando falta el 605 y cuál es el trámite exacto. Solo importa cuando CEN timbre CFDI, lo cual hoy está fuera de alcance.

**¿Y si en vez de recibir nómina te factura honorarios desde RESICO?** Eso **no es nómina**:

- Él emite una factura (CFDI de ingreso).
- Si la empresa es persona moral, le retiene **1.25% de ISR** (art. 113-J) ✔.
- No hay IMSS ni recibo de nómina.
- CEN no debería procesar esto como nómina; sería un pago a proveedor.
- ⚠ Riesgo laboral: si en la práctica tiene jefe, horario y lugar de trabajo, puede considerarse relación de trabajo aunque facture (LFT art. 20). Conviene revisarlo con un contador o abogado.

**Otras obligaciones del trabajador** (fuera del alcance de CEN): su declaración anual de RESICO y la de sueldos.

---

## 3. Catálogo `c_TipoRegimen` (complemento de nómina 1.2)

Las claves y nombres salen de la guía de llenado del SAT ✔ (campo TipoRegimen y Apéndice 6).

| Clave | Descripción SAT | Fundamento LISR | ¿Hay relación laboral? |
|---|---|---|---|
| 02 | Sueldos | art. 94, primer párrafo y fr. I | Sí |
| 03 | Jubilados | art. 93 fr. IV | Ex-trabajador |
| 04 | Pensionados | art. 93 fr. IV | Ex-trabajador |
| 05 | Asimilados Miembros Sociedades Cooperativas Producción | art. 94 fr. II | No |
| 06 | Asimilados Integrantes Sociedades Asociaciones Civiles | art. 94 fr. II | No |
| 07 | Asimilados Miembros consejos | art. 94 fr. III | No |
| 08 | Asimilados comisionistas | art. 94 (fracción ⚠ SIN VERIFICAR) | No |
| 09 | Asimilados Honorarios | art. 94 fr. IV y V | No |
| 10 | Asimilados acciones | art. 94 fr. VII | No |
| 11 | Asimilados otros | art. 94 (resto) | No |
| 12 | Jubilados o Pensionados | art. 93 fr. IV | Ex-trabajador |
| 13 | Indemnización o Separación | arts. 93 fr. XIII, 95 y 96 | Fin de la relación |
| 99 | Otro Régimen | — | — |

**Regla del SAT** ✔:

- Si `TipoContrato` está entre 01 y 08 (contratos laborales), `TipoRegimen` debe ser 02, 03 o 04.
- Si `TipoContrato` es 09 o mayor, `TipoRegimen` va de 05 a 99.

Los pagos por indemnización o separación se marcan con 13. Pueden ir en un CFDI aparte o en el mismo CFDI con dos complementos ✔.

---

## 4. Tabla comparativa por tipo

| | **02 Sueldos** (CEN hoy) | **09 Asimilados honorarios** (y 05–11 en general) | **13 Indemnización o separación** | **03/04/12 Jubilados y pensionados** |
|---|---|---|---|---|
| **ISR** | Tabla del art. 96 (Anexo 8 RMF 2026) ✔ | Misma tabla del art. 96 ✔. Excepción: a los consejeros (07) se les retiene al menos 35%, salvo que también sean trabajadores del mismo patrón ✔ | Tasa = ISR del último sueldo mensual ordinario ÷ ese sueldo. Si el pago es menor que ese sueldo, se usa la tabla ✔ (art. 96) | Exento hasta 15 UMA diarias ✔ (art. 93 fr. IV) |
| **Exentos** | Aguinaldo 30 UMA, prima vacacional y PTU 15 UMA cada una, horas extra ✔ (art. 93) | **Ninguno de esos**: la exención del art. 93 fr. XIV es para "trabajadores de sus patrones" ✔. Todo es gravado | 90 UMA por año de servicio ✔ (art. 93 fr. XIII) | Ver ISR |
| **IMSS (obrero y patronal)** | Sí ✔ | **No**: sin relación laboral no es sujeto obligatorio. La guía dice que registro patronal, NSS, SDI y riesgo de puesto no aplican a asimilados ✔ | ⚠ Revisar si integra salario base de cotización | No (lo paga la institución) |
| **INFONAVIT** | Sí, 5% patronal ✔ | **No** | ⚠ Revisar | No |
| **Subsidio para el empleo** | Sí, si el ingreso mensual es ≤ $11,492.66 ✔ | **No**: el decreto solo aplica al art. 94 primer párrafo y fr. I ✔ | No cuenta para el límite ✔ | No |
| **ISN (estatal)** | Sí, con la tasa de cada estado | **Depende del estado.** **SLP: sí** grava los honorarios preponderantes ✔ (ver 4.1). CDMX (art. 156, texto 2024): grava los pagos a administradores, comisarios y consejeros ✔; los honorarios asimilados en general ⚠ | Depende del estado | CDMX: no se grava ✔ (art. 157 fr. IV) |
| **Prestaciones de la LFT** | Aguinaldo, vacaciones, prima vacacional, horas extra | No aplican (no hay relación laboral) | Finiquito y liquidación | — |
| **Recibo o CFDI** | TipoNomina O; receptor 605; TipoContrato 01–08 | Receptor 605; TipoContrato 09+; Sindicalizado "No" ✔ | Normalmente TipoNomina E, PeriodicidadPago 99 ✔ | Lo emite quien paga |

**Subsidio para el empleo 2026** ✔ (decreto del DOF 31-12-2025, que modifica el del 01-05-2024):

- Solo se aplica **contra el ISR**. Si el subsidio es mayor que el ISR, **no se entrega nada en efectivo**.
- Monto: 15.02% de la UMA mensual → **$535.65** de febrero a diciembre. En enero: 15.59% de la UMA 2025 → **$536.21**.
- Límite de ingreso mensual: **$11,492.66**. No cuentan para el límite las primas de antigüedad, retiro e indemnizaciones.
- Para periodos menores a un mes: subsidio mensual ÷ 30.4 × días del periodo.

**Salario mínimo:**

- Si el trabajador solo gana el salario mínimo, **no se le retiene ISR** ✔ (art. 96).
- Su cuota obrera del IMSS la paga el patrón (LSS art. 36) ⚠ no re-verificado en esta investigación.

### 4.1 Impuesto sobre nóminas en San Luis Potosí

En SLP se llama **ISERTP** (Impuesto sobre Erogaciones por Remuneración al Trabajo Personal). Se paga cada mes, a más tardar el día 15 del mes siguiente ✔ (Secretaría de Finanzas de SLP).

Según el texto de la Ley de Hacienda para el Estado de SLP que pude leer (arts. 20 a 27, **versión con última reforma del 20-11-2008**):

- **Qué se grava** (art. 20) ✔:
  - fr. I: salarios y toda remuneración que venga de una relación laboral
  - fr. II: honorarios y pagos a administradores, comisarios y consejeros
  - fr. III: **honorarios a personas que presten servicios profesionales en forma preponderante al contribuyente**, en los términos de la LISR
- **Conclusión:** en SLP los **asimilados por honorarios (09) sí pagan ISN**. Es distinto de CDMX.
- **Base** (art. 22) ✔: el total de las remuneraciones, sin los conceptos que la LSS excluye del salario base de cotización.
- **Tasa:** esa versión dice 2% (art. 23). Fuentes secundarias actuales dicen **3%**. ⚠ SIN VERIFICAR la tasa vigente para 2026: el texto oficial actualizado (Congreso de SLP, reforma al 24-12-2025) no se pudo descargar. Hay que confirmarlo antes de sembrar la tasa en `state_payroll_tax_rates`.
- **Exenciones relevantes** (art. 27) ✔: gastos de representación y viáticos comprobados, instituciones de asistencia autorizadas, sindicatos y escuelas gratuitas.
- **Estímulo** (art. 28) ✔: empresas de nueva creación, hasta 100% del ISN el primer año.
- ⚠ Revisar en el texto vigente que el art. 20 fr. III siga igual.

---

## 5. Otros datos que cambian el cálculo o el recibo

| Catálogo | Valores | ¿Afecta el cálculo de CEN? |
|---|---|---|
| `c_TipoNomina` ✔ | O Ordinaria, E Extraordinaria (aguinaldo, bonos, separación) | Sí: la extraordinaria debe usar PeriodicidadPago 99 ✔ |
| `c_PeriodicidadPago` ✔ | 01 Diario, 02 Semanal, 03 Catorcenal, 04 Quincenal, 05 Mensual, 06 Bimestral, 07 Unidad de obra, 08 Comisión, 09 Precio alzado, 10 Decenal, 99 Otra | Sí. CEN hoy solo tiene 02, 04 y 05 |
| `c_TipoContrato` | 01 a 08 son contratos laborales ✔ (indeterminado, obra determinada, tiempo determinado, temporada, a prueba, capacitación inicial, por hora, comisión). 09+ son sin relación laboral ✔; nombres exactos de 09, 10 y 99 ⚠ | Solo define qué tipo de régimen se permite |
| `c_TipoJornada` | 01 Diurna ✔; el resto (nocturna, mixta, por hora, etc.) ⚠ | Sí, en horas extra: la jornada nocturna es de 7 h y la mixta de 7.5 h (LFT art. 61); CEN asume 8 h |
| Sindicalizado ✔ | Sí / No (asimilados siempre "No") | No |
| `c_RiesgoPuesto` ✔ | Clase I–V; 99 No aplica (no afiliados al IMSS) | Solo afecta el costo patronal (prima de riesgo) |
| Zona del salario mínimo ✔ | General $315.04 / Zona Libre de la Frontera Norte $440.87 diarios (2026) | Sí: el piso del salario base de cotización y el caso de salario mínimo |

---

## 6. Valores 2026 comparados con el código

| Dato | Valor oficial 2026 | ¿Qué tiene CEN? | ¿Coincide? |
|---|---|---|---|
| Tabla mensual de ISR del art. 96 | Anexo 8 RMF 2026 (DOF 28-12-2025), 11 renglones, de 0.01–844.59 al 1.92% hasta 425,642.00 en adelante al 35% | `ISR_TABLE` en [payroll_controller.py:33](../server/src/controllers/payroll_controller.py) | ✔ Coincide renglón por renglón |
| UMA | $117.31 diaria / $3,566.22 mensual desde el 01-02-2026 (INEGI, DOF 09-01-2026). En enero rige la UMA 2025 | `UMA_MENSUAL = 3566.22` ([payroll_controller.py:5](../server/src/controllers/payroll_controller.py)) y en la BD con fechas de vigencia (migración 012) | ✔ Coincide (el código no maneja enero) |
| Límite del subsidio | $11,492.66 | `ISR_SUBSIDIO_LIMITE` | ✔ Coincide |
| Monto del subsidio | $535.65 (feb–dic) / $536.21 (enero) | `ISR_SUBSIDIO_MONTO = 536.22` | ✘ Diferencia de $0.57 al mes (ver 7.3) |
| Salario mínimo general | $315.04 | En la BD (migración 012) | ✔ Coincide |
| Salario mínimo de la frontera | $440.87 | No existe | — |
| Tasas de la cuota obrera del IMSS | 0.25% / 0.375% / 0.625% / 1.125% / 0.40% sobre el excedente de 3 UMA | Constantes `IMSS_*` | Coinciden con la LSS (no re-verificado aquí) |

---

## 7. Impacto en CEN

### 7.1 Estado actual

- Solo se calcula `02 Sueldos`, con periodicidad mensual, quincenal o semanal.
- El empleado no tiene tipo de régimen ([payroll_model.py](../server/src/models/payroll_model.py)).
- El cálculo usa estrategias (`ISRStrategy`, `IMSSStrategy`), y el costo patronal ([employer_cost.py](../server/src/controllers/employer_cost.py)) ya lee sus parámetros de la BD con vigencia y fuente.
- El ISN está pendiente porque falta la tasa de cada estado.

### 7.2 Cambios propuestos para el MVP (02 + 09)

> **Estado (fase 6, 26-09-2026):** implementado tal como se describe abajo, más el tipo de jornada (migración 014).

**Base de datos (migración 013)**

- `employees.tipo_regimen CHAR(2) NOT NULL DEFAULT '02' CHECK (tipo_regimen IN ('02','09'))`. Los empleados que ya existen quedan como 02 sin tener que migrar datos.
- `payroll_receipts.tipo_regimen CHAR(2) NOT NULL DEFAULT '02'`. Es una foto del régimen al momento de calcular: si mañana cambia el régimen del empleado, sus recibos anteriores no cambian. Es el mismo criterio que ya usa el costo patronal guardado.

**Modelos (Pydantic)**

- `TipoRegimen = Literal["02", "09"]` en `Employee`, `EmployeeCreateRequest` y `EmployeeUpdateRequest`.
- Solo tiene sentido para el rol `employee`; los admins no cobran nómina.

**Cálculo ([payroll_controller.py](../server/src/controllers/payroll_controller.py))**

- `ISRStrategy` recibe si aplica el subsidio: sí para 02, no para 09.
- Para 09 se usa una estrategia sin IMSS, y el renglón de IMSS no aparece en el recibo (no un renglón en $0). Hay que ajustar `process()`, que hoy busca ese renglón con `next(...)`.
- Para 09, la API rechaza y la pantalla oculta: horas extra, días de aguinaldo, días de vacaciones y crédito Infonavit. Son figuras de la relación laboral. Se mantienen el bono (todo gravado) y el préstamo.

**Costo patronal ([employer_cost.py](../server/src/controllers/employer_cost.py))**

- Para 09, los componentes de IMSS, SAR e INFONAVIT quedan como **"no aplica"**. No deben quedar como "pendiente" (`missing`), porque son cosas distintas: una no existe y la otra falta calcularla.
- El ISN depende del estado. Propuesta: un dato por estado que diga si grava a los asimilados. En SLP sí los grava (sección 4.1); los demás estados quedan como pendiente hasta confirmarlos.

**Recibo PDF y ReceiptCard**

- Mostrar el tipo de régimen.
- Para 09: título "Recibo de honorarios asimilados a salarios" y sin renglón de IMSS.

**Pantallas**

- Un select "Tipo de nómina" (Sueldos y salarios / Asimilados a salarios) en el alta ([SignupPage.tsx](../client/src/pages/SignupPage.tsx)) y en la edición ([EmployeesPage.tsx](../client/src/pages/EmployeesPage.tsx)). Solo aparece si el rol es Empleado.
- La calculadora del admin oculta los campos que no aplican.
- Actualizar los tipos en `employeeService.ts` y `payrollService.ts`.

**Pruebas**

- Un asimilado no tiene IMSS ni subsidio, y todo le queda gravado.
- Rechazar horas extra y aguinaldo para un asimilado.
- Los recibos de 02 salen igual que hoy.
- Los empleados existentes quedan como 02 después de la migración.
- Un asimilado no tiene IMSS/SAR/INFONAVIT en el costo patronal.

**Qué NO hace falta todavía:** RFC, CURP, NSS, TipoContrato, TipoJornada, riesgo de puesto y sindicalizado. Son obligatorios para **timbrar** el CFDI, no para **calcular**. Conviene agregarlos cuando se planee el timbrado.

### 7.3 Hallazgos del código actual (fuera de alcance; no los toqué)

> **Estado (fase 5, 25-09-2026):**
> - Los puntos 1 a 4 están corregidos: el subsidio y la UMA se leen con vigencia (2025 y 2026, migración 013), el IMSS se calcula sobre el SBC y el caso de salario mínimo ya existe.
> - El 5 (jornada) quedó resuelto en la fase 6.
> - El 6 sigue pendiente de confirmar con un contador.

1. **Monto del subsidio.** `ISR_SUBSIDIO_MONTO = 536.22` ([payroll_controller.py:31](../server/src/controllers/payroll_controller.py)). De febrero a diciembre de 2026 son $535.65; en enero, $536.21. El código resta $0.57 de más al mes a quien tiene subsidio.
2. **Valores sin fecha de vigencia.** La UMA y el subsidio están fijos en el código, mientras que el costo patronal los lee de la BD con vigencia. Cada año habrá que cambiar el código, y los cálculos de enero usan la UMA equivocada.
3. **Base del IMSS obrero.** Se calcula sobre el sueldo del periodo (`imss_calc.calculate(gross_salary)`), no sobre el salario base de cotización integrado que ya calcula el costo patronal. Esto puede dejar la retención corta.
4. **Caso de salario mínimo.** No existe: a quien gana solo el mínimo no se le debe retener ISR, y su cuota obrera del IMSS la paga el patrón.
5. **Horas de jornada.** Se asumen 8 h (`HORAS_DE_JORNADA`) para el salario por hora de las horas extra. Las jornadas nocturna (7 h) y mixta (7.5 h) dan otro valor.
6. **Base del límite del subsidio.** El límite se compara contra las percepciones gravadas. El decreto habla de "ingresos". ⚠ Confirmarlo con un contador.

---

## 8. Recomendación priorizada

**Ya (MVP)**

- `02 Sueldos` (ya existe) + `09 Asimilados honorarios`.
  **Por qué:** son las dos figuras más comunes en empresas pequeñas y medianas. 09 usa la misma tabla de ISR y, sobre todo, **quita** cosas (IMSS, subsidio, exenciones), así que el riesgo es bajo.

**Después, en este orden**

1. **Nómina extraordinaria** (TipoNomina E): aguinaldo y PTU como pagos aparte.
2. **13 Indemnización o separación** (finiquito y liquidación): necesita antigüedad, último sueldo mensual ordinario y exención de 90 UMA por año.
3. **Periodicidades catorcenal, decenal y diaria.**
4. **Caso de salario mínimo y Zona Libre de la Frontera Norte.**
5. **07 Consejeros:** retención mínima del 35%.

**Fuera de alcance, con su porqué**

- **03/04/12 Jubilados y pensionados:** normalmente los paga el IMSS, una aseguradora o un fideicomiso, no la empresa.
- **05/06 Cooperativas y asociaciones civiles, 10 Acciones, 11 Otros:** casos poco comunes y cada uno con sus propias reglas.
- **Honorarios facturados desde RESICO:** no es nómina; son pagos a proveedor con retención del 1.25%.
- **Timbrado del CFDI:** requiere un PAC, sellos digitales (CSD) y los datos fiscales del trabajador. Es un proyecto en sí mismo.
- **Declaración anual del trabajador:** le toca al trabajador, no al patrón.

---

## 9. Fuentes

| Fuente | Qué se confirmó |
|---|---|
| SAT, [Guía de llenado del CFDI de nómina 4.0 / complemento 1.2](http://omawww.sat.gob.mx/tramitesyservicios/Paginas/documentos/Guia_llenado_Nomina.pdf) (versión 6, 08-03-2023) | Régimen del receptor 605, catálogos, regla TipoContrato ↔ TipoRegimen, qué no aplica a asimilados, TipoNomina E con periodicidad 99 |
| Cámara de Diputados, [Ley del ISR](https://www.diputados.gob.mx/LeyesBiblio/pdf/LISR.pdf) (última reforma DOF 01-04-2024) | Arts. 93 fr. IV, XIII y XIV; 94; 96; 113-E; 113-J |
| DOF, [Decreto del subsidio para el empleo 2026](https://dof.gob.mx/nota_detalle.php?codigo=5777649&fecha=31%2F12%2F2025) (31-12-2025) | Límite $11,492.66, 15.02% de la UMA, 15.59% en enero, periodos menores a un mes |
| DOF, [Decreto del subsidio para el empleo](https://dof.gob.mx/nota_detalle.php?codigo=5725287&fecha=01%2F05%2F2024) (01-05-2024) | Solo art. 94 primer párrafo y fr. I; sin entrega en efectivo |
| SAT, [Anexo 8 RMF 2026](https://www.sat.gob.mx/minisitio/NormatividadRMFyRGCE/documentos2026/rmf/anexos/Anexo-8-RMF-2026_DOF-28122025.pdf) (DOF 28-12-2025) | Tabla mensual de ISR del art. 96 |
| INEGI, [UMA 2026](https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2026/uma/uma2026.pdf) / [DOF 09-01-2026](https://dof.gob.mx/nota_detalle.php?codigo=5778072&fecha=09%2F01%2F2026) | UMA $117.31 / $3,566.22 desde 01-02-2026 |
| CONASAMI, [Incremento a los salarios mínimos 2026](https://www.gob.mx/conasami/articulos/incremento-a-los-salarios-minimos-para-2026?idiom=es) | $315.04 general / $440.87 frontera |
| Congreso de SLP, [Ley de Hacienda para el Estado de SLP](https://docs.mexico.justia.com/estatales/san-luis-potosi/ley-de-hacienda-para-el-estado-de-san-luis-potosi.pdf) (compilación con última reforma del 20-11-2008) | ISN de SLP, arts. 20–28: objeto (incluye honorarios preponderantes), base, exenciones y estímulo. Tasa ⚠ desactualizada |
| Secretaría de Finanzas de SLP, [ISERTP](https://finanzas.slp.gob.mx/isertp/) | Nombre del impuesto y fecha de pago (día 15) |
| Finanzas CDMX, [Código Fiscal de la CDMX, arts. 156–157](https://transparencia.finanzas.cdmx.gob.mx/repositorio/public/upload/repositorio/Tesoreria/123/b/Criterio_9/123_XV_Impuesto_sobre_nominas_2024.pdf) (texto 2024) | Qué pagos grava y cuáles excluye el ISN en CDMX |
| [Calcu.mx](https://calcu.mx/subsidio-al-empleo/2026) / [El Contribuyente](https://www.elcontribuyente.mx/2026/01/subsidio-para-el-empleo-2026-cuanto-recibiras-con-el-nuevo-aumento/) (secundarias) | Montos $535.65 / $536.21, que coinciden con el cálculo sobre el decreto |
