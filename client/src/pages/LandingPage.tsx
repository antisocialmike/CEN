import {
  startTransition,
  useEffect,
  useId,
  useMemo,
  useState
} from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion, useReducedMotion } from "motion/react";
import {
  ArrowRight,
  Certificate,
  Check,
  ClockCounterClockwise,
  FileText,
  Lock,
  Scales,
  ShieldCheck,
  UsersThree
} from "@phosphor-icons/react";
import { LogoMark } from "../components/icons";
import ThemeToggle from "../components/ThemeToggle";
import NetoDelPeriodo, { type Partida } from "../components/landing/NetoDelPeriodo";
import {
  desglosar,
  ETIQUETA_PERIODICIDAD,
  type Periodicidad
} from "../components/landing/calculoNomina";
import { formatCurrency } from "../services/format";
import { EASE_OUT } from "../motion/variants";
import "lenis/dist/lenis.css";
import "../styles/skin-landing.css";

const BRUTO_EJEMPLO = 22000;
const PERIODICIDAD_EJEMPLO: Periodicidad = "mensual";

const RECIBOS = [
  { mes: "Agosto 2026", folio: "128", bruto: 22000 },
  { mes: "Julio 2026", folio: "111", bruto: 22000 },
  { mes: "Junio 2026", folio: "94", bruto: 21000 },
  { mes: "Mayo 2026", folio: "77", bruto: 19500 }
];

const CONFIANZA = [
  {
    icono: <Scales weight="bold" />,
    titulo: "Tablas vigentes, no un porcentaje",
    detalle: "El ISR sale de la tarifa por rangos y aplica el subsidio al empleo."
  },
  {
    icono: <FileText weight="bold" />,
    titulo: "Recibo en PDF tamaño Carta",
    detalle: "Con folio y periodo únicos, listo para imprimir o archivar."
  },
  {
    icono: <ClockCounterClockwise weight="bold" />,
    titulo: "Dar de baja no borra nada",
    detalle: "La baja es lógica: el histórico de recibos se conserva completo."
  },
  {
    icono: <Lock weight="bold" />,
    titulo: "El permiso se verifica en el servidor",
    detalle: "Nunca en la interfaz, así que no se puede saltar desde el navegador."
  },
  {
    icono: <Certificate weight="bold" />,
    titulo: "Es un comprobante interno, no un CFDI",
    detalle: "Cada PDF lo dice impreso. Timbrar exige un PAC y no lo hacemos."
  }
];

const FLUJO = [
  "La petición llega firmada, con la identidad de quien la hace dentro.",
  "El servidor comprueba la firma y que no haya caducado.",
  "Comprueba que ese rol tenga permiso para lo que está pidiendo.",
  "Solo entonces salen los datos."
];

const ANCLAS = ["calculo", "roles", "seguridad"] as const;

const ETIQUETA_ANCLA: Record<(typeof ANCLAS)[number], string> = {
  calculo: "El cálculo",
  roles: "Roles",
  seguridad: "Seguridad"
};

function useSeccionVisible() {
  const [activa, setActiva] = useState<string | null>(null);

  useEffect(() => {
    const secciones = ANCLAS.map((id) => document.getElementById(id)).filter(
      (n): n is HTMLElement => n !== null
    );
    if (secciones.length === 0) return;

    const observador = new IntersectionObserver(
      (entradas) => {
        const visible = entradas
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (visible) setActiva(visible.target.id);
      },
      { rootMargin: "-72px 0px -50% 0px", threshold: [0, 0.25, 0.5] }
    );

    secciones.forEach((s) => observador.observe(s));
    return () => observador.disconnect();
  }, []);

  return activa;
}

function useScrollSuave(activo: boolean) {
  useEffect(() => {
    if (!activo) return;

    if (typeof ResizeObserver === "undefined") return;

    let lenis: import("lenis").default | null = null;
    let cancelado = false;
    let fotograma = 0;

    const alPulsarAncla = (evento: MouseEvent) => {
      const destino = (evento.target as HTMLElement | null)?.closest<HTMLAnchorElement>(
        'a[href^="#"]'
      );
      if (!destino || !lenis) return;

      const id = destino.getAttribute("href")?.slice(1);
      if (!id) return;
      const seccion = document.getElementById(id);
      if (!seccion) return;

      evento.preventDefault();

      seccion.focus({ preventScroll: true });
      history.replaceState(null, "", `#${id}`);

      lenis.scrollTo(seccion);
    };

    void import("lenis")
      .then(({ default: Lenis }) => {
        if (cancelado) return;

        lenis = new Lenis({ duration: 0.9, wheelMultiplier: 1, touchMultiplier: 1.6 });

        const latido = (tiempo: number) => {
          lenis?.raf(tiempo);
          fotograma = requestAnimationFrame(latido);
        };
        fotograma = requestAnimationFrame(latido);

        document.addEventListener("click", alPulsarAncla);
      })
      .catch(() => {});

    return () => {
      cancelado = true;
      cancelAnimationFrame(fotograma);
      document.removeEventListener("click", alPulsarAncla);
      lenis?.destroy();
      lenis = null;
    };
  }, [activo]);
}

function Calculadora() {
  const idSueldo = useId();
  const idPeriodo = useId();
  const [bruto, setBruto] = useState(String(BRUTO_EJEMPLO));
  const [periodicidad, setPeriodicidad] = useState<Periodicidad>(PERIODICIDAD_EJEMPLO);

  const desglose = useMemo(
    () => desglosar(Number(bruto.replace(/[^\d.]/g, "")), periodicidad),
    [bruto, periodicidad]
  );

  const retenido = desglose.isr + desglose.imss;
  const anchoDe = (importe: number) =>
    desglose.bruto > 0 ? `${(importe / desglose.bruto) * 100}%` : "0%";

  return (
    <div className="rv-calc">
      <div className="rv-calc-mandos">
        <div className="rv-campo">
          <label htmlFor={idSueldo}>Salario bruto</label>
          <div className="rv-campo-caja">
            <span className="rv-campo-prefijo" aria-hidden="true">
              $
            </span>
            <input
              id={idSueldo}
              type="text"
              inputMode="decimal"
              value={bruto}
              onChange={(evento) => setBruto(evento.target.value)}
              aria-describedby={`${idSueldo}-pista`}
            />
          </div>
          <p className="rv-campo-pista" id={`${idSueldo}-pista`}>
            Escribe el sueldo de alguien de tu equipo. No se guarda nada.
          </p>
        </div>

        <div className="rv-campo">
          <label htmlFor={idPeriodo}>Periodicidad</label>
          <div className="rv-campo-caja">
            <select
              id={idPeriodo}
              value={periodicidad}
              onChange={(evento) => setPeriodicidad(evento.target.value as Periodicidad)}
            >
              {(Object.keys(ETIQUETA_PERIODICIDAD) as Periodicidad[]).map((clave) => (
                <option key={clave} value={clave}>
                  {ETIQUETA_PERIODICIDAD[clave]}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

            <figure className="rv-cascada">
        <figcaption className="rv-cascada-titulo">
          De cada {formatCurrency(desglose.bruto)}, se retienen{" "}
          {formatCurrency(retenido)}.
        </figcaption>

        <div
          className="rv-cascada-barra"
          role="img"
          aria-label={
            `De un bruto de ${formatCurrency(desglose.bruto)}: ` +
            `ISR ${formatCurrency(desglose.isr)}, ` +
            `IMSS ${formatCurrency(desglose.imss)}, ` +
            `neto ${formatCurrency(desglose.neto)}.`
          }
        >
          <span
            className="rv-cascada-tramo"
            data-serie="neto"
            style={{ width: anchoDe(desglose.neto) }}
          />
          <span
            className="rv-cascada-tramo"
            data-serie="isr"
            style={{ width: anchoDe(desglose.isr) }}
          />
          <span
            className="rv-cascada-tramo"
            data-serie="imss"
            style={{ width: anchoDe(desglose.imss) }}
          />
        </div>

        <ul className="rv-leyenda">
          <li data-serie="neto">
            <span className="rv-leyenda-marca" aria-hidden="true" />
            Neto <b>{formatCurrency(desglose.neto)}</b>
          </li>
          <li data-serie="isr">
            <span className="rv-leyenda-marca" aria-hidden="true" />
            ISR <b>{formatCurrency(desglose.isr)}</b>
          </li>
          <li data-serie="imss">
            <span className="rv-leyenda-marca" aria-hidden="true" />
            IMSS <b>{formatCurrency(desglose.imss)}</b>
          </li>
        </ul>
      </figure>

      <p className="rv-calc-nota">
        La misma fórmula que corre en el servidor cuando calculas la nómina de verdad.
        El subsidio al empleo ya está aplicado.
      </p>
    </div>
  );
}

export default function LandingPage() {
  const navigate = useNavigate();
  const reduce = useReducedMotion();
  const seccionActiva = useSeccionVisible();
  useScrollSuave(!reduce);

  const irALogin = () => startTransition(() => navigate("/login"));

  const ejemplo = useMemo(
    () => desglosar(BRUTO_EJEMPLO, PERIODICIDAD_EJEMPLO),
    []
  );

  const recibos = useMemo(
    () => RECIBOS.map((r) => ({ ...r, ...desglosar(r.bruto, "mensual") })),
    []
  );

  const partidasEjemplo: Partida[] = [
    { concepto: "Salario bruto", importe: ejemplo.bruto, tipo: "percepcion" },
    { concepto: "ISR retenido", importe: ejemplo.isr, tipo: "deduccion" },
    { concepto: "IMSS retenido", importe: ejemplo.imss, tipo: "deduccion" }
  ];

  return (
    <div className="rv-lp">
      <a className="skip-link" href="#contenido">
        Ir al contenido
      </a>

      <header className="rv-nav">
        <div className="rv-wrap rv-nav-inner">
          <Link className="brand-logo" to="/">
            <LogoMark />
            <div className="brand-logo-text">
              <span>CEN Payroll</span>
              <small>Sistema de nómina</small>
            </div>
          </Link>

          <nav className="rv-nav-links" aria-label="Secciones">
            {ANCLAS.map((id) => (
              <a
                key={id}
                href={`#${id}`}
                data-activa={seccionActiva === id ? "" : undefined}
                aria-current={seccionActiva === id ? "true" : undefined}
              >
                {ETIQUETA_ANCLA[id]}
              </a>
            ))}
          </nav>

          <ThemeToggle />

          <button
            className="btn btn-rosa"
            onClick={irALogin}
          >
            Iniciar sesión
          </button>
        </div>
      </header>

      <main id="contenido" tabIndex={-1}>
                <section className="rv-hero">
          <div className="rv-wrap rv-hero-grid">
            <motion.div
              className="rv-hero-copy"
              initial={reduce ? false : { opacity: 0, transform: "translateY(18px)" }}
              animate={{ opacity: 1, transform: "translateY(0px)" }}
              transition={{ duration: 0.55, ease: EASE_OUT }}
            >
              <h1>Nómina que cuadra.</h1>
              <p className="rv-hero-sub">
                Calculas el bruto. CEN devuelve el ISR, el IMSS y el neto — de las tablas
                vigentes, no de un porcentaje fijo.
              </p>
              <div className="rv-hero-acciones">
                <button
                  className="btn btn-rosa"
                  onClick={irALogin}
                >
                  Iniciar sesión
                </button>
                <a className="btn btn-line" href="#calculo">
                  Ver el cálculo
                </a>
              </div>
            </motion.div>

            <motion.div
              className="rv-hero-resta"
              initial={reduce ? false : { opacity: 0, transform: "translateY(24px)" }}
              animate={{ opacity: 1, transform: "translateY(0px)" }}
              transition={{ duration: 0.6, ease: EASE_OUT, delay: reduce ? 0 : 0.12 }}
            >
              <ol className="rv-carril">
                <li className="rv-paso">
                  <span className="rv-paso-et">Salario bruto</span>
                  <span className="rv-paso-v">{formatCurrency(ejemplo.bruto)}</span>
                </li>
                <li className="rv-paso" data-tipo="deduccion">
                  <span className="rv-paso-et">ISR retenido</span>
                  <span className="rv-paso-v">
                    <span aria-hidden="true">− </span>
                    {formatCurrency(ejemplo.isr)}
                  </span>
                </li>
                <li className="rv-paso" data-tipo="deduccion">
                  <span className="rv-paso-et">IMSS retenido</span>
                  <span className="rv-paso-v">
                    <span aria-hidden="true">− </span>
                    {formatCurrency(ejemplo.imss)}
                  </span>
                </li>
                <li className="rv-paso rv-paso--total">
                  <span className="rv-paso-et">Neto a pagar</span>
                  <span className="rv-paso-v">{formatCurrency(ejemplo.neto)}</span>
                </li>
              </ol>
              <p className="rv-hero-pie">
                Un mes de {formatCurrency(ejemplo.bruto)}, con el subsidio al empleo aplicado.
              </p>
            </motion.div>
          </div>
        </section>

                <section className="rv-confianza">
          <div className="rv-wrap">
            <ul className="rv-confianza-lista">
              {CONFIANZA.map((punto) => (
                <li key={punto.titulo}>
                  <span className="rv-confianza-icono" aria-hidden="true">
                    {punto.icono}
                  </span>
                  <h2>{punto.titulo}</h2>
                  <p>{punto.detalle}</p>
                </li>
              ))}
            </ul>
          </div>
        </section>

                <section className="rv-seccion" id="calculo" tabIndex={-1}>
          <div className="rv-wrap rv-calc-grid">
            <div className="rv-seccion-cabecera">
              <h2>Compruébalo con el sueldo de tu equipo.</h2>
              <p>
                Cambia la cifra y mira cómo se mueven el ISR y el IMSS. Sin cuenta, sin
                registro, sin que salga de tu navegador.
              </p>
            </div>

            <Calculadora />
          </div>
        </section>

                <section className="rv-seccion rv-seccion--alt">
          <div className="rv-wrap rv-recibo-grid">
            <div className="rv-seccion-cabecera">
              <h2>Y esto es lo que recibe.</h2>
              <p>
                Cada cálculo se guarda con su folio y su periodo. El empleado entra a su
                portal y lo tiene, sin pedirlo por correo.
              </p>
            </div>

            <div className="rv-recibo-muestra">
              <NetoDelPeriodo
                neto={ejemplo.neto}
                empleado="Ana Gutiérrez"
                periodo="1 al 31 de agosto de 2026"
                folio="128"
                partidas={partidasEjemplo}
              />
            </div>
          </div>
        </section>

                <section className="rv-seccion">
          <div className="rv-wrap">
            <div className="rv-seccion-cabecera">
              <h2>El historial no se pierde.</h2>
              <p>Desde el primer recibo, con su folio y su fecha.</p>
            </div>
          </div>
          <div className="rv-wrap">
            <ul className="rv-carril-recibos" tabIndex={0} aria-label="Recibos de ejemplo">
              {recibos.map((r) => (
                <li key={r.folio}>
                  <NetoDelPeriodo
                    neto={r.neto}
                    empleado={r.mes}
                    periodo={`Bruto ${formatCurrency(r.bruto)}`}
                    folio={r.folio}
                    variante="compacta"
                  />
                </li>
              ))}
            </ul>
          </div>
        </section>

                <section className="rv-seccion rv-seccion--alt" id="roles" tabIndex={-1}>
          <div className="rv-wrap">
            <div className="rv-seccion-cabecera">
              <h2>Cada quien entra a lo suyo.</h2>
            </div>

            <div className="rv-roles">
              <article className="rv-rol">
                <span className="rv-rol-icono" aria-hidden="true">
                  <UsersThree weight="bold" />
                </span>
                <h3>Administrador</h3>
                <p>Da de alta al equipo, calcula la nómina y ve los recibos de todos.</p>
                <ul>
                  <li>
                    <Check weight="bold" /> Alta de empleados con salario base
                  </li>
                  <li>
                    <Check weight="bold" /> Cálculo de ISR e IMSS por periodo
                  </li>
                  <li>
                    <Check weight="bold" /> Historial completo del equipo
                  </li>
                </ul>
              </article>

              <article className="rv-rol">
                <span className="rv-rol-icono" aria-hidden="true">
                  <FileText weight="bold" />
                </span>
                <h3>Empleado</h3>
                <p>Entra a su propio portal y encuentra sus recibos. Nada más, nada menos.</p>
                <ul>
                  <li>
                    <Check weight="bold" /> Sus recibos, desde el primero
                  </li>
                  <li>
                    <Check weight="bold" /> Desglose de lo que se retuvo
                  </li>
                  <li>
                    <Check weight="bold" /> Sin pedirlo por correo
                  </li>
                </ul>
              </article>
            </div>
          </div>
        </section>

                <section className="rv-seccion" id="seguridad" tabIndex={-1}>
          <div className="rv-wrap rv-seguridad-grid">
            <div className="rv-seccion-cabecera">
              <h2>El sueldo de tu equipo no es dato público.</h2>
              <p>
                El permiso se verifica en el servidor, nunca en la interfaz. Un empleado pide
                <em> sus</em> recibos, no los de alguien en concreto: el sistema saca de quién
                son a partir de su sesión, así que no hay dirección que escribir a mano.
              </p>
            </div>

            <ol className="rv-flujo">
              {FLUJO.map((paso, indice) => (
                <li key={paso}>
                  <span className="rv-flujo-icono" aria-hidden="true">
                    {indice === FLUJO.length - 1 ? (
                      <ShieldCheck weight="bold" />
                    ) : (
                      <Check weight="bold" />
                    )}
                  </span>
                  {paso}
                </li>
              ))}
            </ol>
          </div>
        </section>

                <section className="rv-cierre">
          <div className="rv-wrap">
            <h2>Tu próxima nómina, en dos minutos.</h2>
            <p>Entra para calcular la nómina de tu equipo o para consultar tus recibos.</p>
            <button
              className="btn btn-rosa"
              onClick={irALogin}
            >
              Iniciar sesión
              <ArrowRight weight="bold" />
            </button>
          </div>
        </section>

                <section className="rv-seccion rv-seccion--alt" id="legal" tabIndex={-1}>
          <div className="rv-wrap rv-legal">
            <h2>Aviso de privacidad y términos</h2>
            <p className="rv-legal-intro">
              Redactado sobre lo que el sistema hace hoy, verificado contra el esquema de la
              base de datos y el código del servidor. Aun así es un borrador: antes de
              publicarse lo tiene que revisar alguien calificado, y faltan los datos del
              responsable.
            </p>

            <details className="rv-detalle">
              <summary>Aviso de privacidad</summary>
              <div className="rv-detalle-cuerpo">
                <p className="rv-legal-fecha">
                  Última actualización: 14 de septiembre de 2026
                </p>

                <h3>1. Quién es el responsable</h3>
                <p>
                  <b>[RAZÓN SOCIAL]</b>, con domicilio en <b>[DOMICILIO FISCAL]</b>, es
                  responsable del tratamiento de los datos personales que se registran en CEN
                  Payroll, en términos de la Ley Federal de Protección de Datos Personales en
                  Posesión de los Particulares y su Reglamento.
                </p>

                <h3>2. Qué datos se tratan</h3>
                <p>De cada persona dada de alta:</p>
                <ul>
                  <li>
                    <b>Identificación y contacto:</b> nombre completo y correo electrónico.
                  </li>
                  <li>
                    <b>Laborales:</b> rol dentro de la organización, salario base, periodicidad
                    de pago y situación de alta o baja.
                  </li>
                  <li>
                    <b>Patrimoniales:</b> los importes de cada recibo — percepciones,
                    deducciones de ISR e IMSS, base gravable y neto — junto con el periodo, los
                    días pagados y quién procesó el cálculo.
                  </li>
                  <li>
                    <b>De acceso:</b> una huella criptográfica irreversible de la contraseña,
                    el número de intentos fallidos de inicio de sesión y, en su caso, la fecha
                    hasta la que la cuenta queda bloqueada.
                  </li>
                </ul>
                <p>
                  <b>El salario y los importes de los recibos son datos patrimoniales.</b> La
                  ley exige para ellos consentimiento expreso, no tácito: al darte de alta, la
                  organización debe recabarlo y conservar constancia.
                </p>
                <p>
                  <b>No se tratan datos personales sensibles.</b> El sistema no pide ni almacena
                  origen racial o étnico, estado de salud, información genética, creencias
                  religiosas, filosóficas o morales, afiliación sindical, opiniones políticas ni
                  preferencia sexual.
                </p>
                <p>
                  <b>Tampoco se recaban</b> RFC, CURP, número de seguridad social, cuenta
                  bancaria o CLABE, domicilio, teléfono ni fecha de nacimiento. Si algún día se
                  añaden, este aviso tiene que actualizarse antes.
                </p>

                <h3>3. Para qué se usan</h3>
                <p>Finalidades primarias, necesarias para prestar el servicio:</p>
                <ul>
                  <li>Calcular las retenciones de ISR e IMSS a partir del salario registrado.</li>
                  <li>Emitir y conservar el comprobante interno de nómina de cada periodo.</li>
                  <li>Autenticar el acceso y decidir qué ve cada persona según su rol.</li>
                  <li>Permitir la recuperación de la contraseña.</li>
                  <li>
                    Proteger las cuentas frente a intentos de acceso no autorizado, mediante el
                    conteo de intentos fallidos y el bloqueo temporal.
                  </li>
                </ul>
                <p>
                  <b>No hay finalidades secundarias.</b> Los datos no se usan para mercadotecnia,
                  publicidad, prospección comercial, elaboración de perfiles ni ninguna otra
                  finalidad distinta de las anteriores.
                </p>

                <h3>4. Cookies y tecnologías de rastreo</h3>
                <p>
                  <b>Este sitio no usa cookies</b> ni balizas web, ni analítica de terceros, ni
                  píxeles de seguimiento, ni publicidad. La aplicación guarda en tu navegador
                  únicamente dos preferencias —el tema claro u oscuro y tu sesión iniciada— que
                  no salen de tu equipo, no identifican a nadie y se borran al cerrar sesión o
                  al limpiar los datos del navegador.
                </p>

                <h3>5. Quién puede ver tus datos</h3>
                <p>
                  El rol de administrador de tu organización accede a los datos de su equipo.
                  Cada persona empleada accede únicamente a los suyos. La verificación ocurre en
                  el servidor en cada petición, no en el navegador.
                </p>

                <h3>6. Transferencias y encargados</h3>
                <p>
                  <b>Los datos no se venden, ceden ni comparten con terceros para fines propios
                  de esos terceros.</b> Sí intervienen dos encargados que tratan datos por
                  cuenta del responsable y bajo sus instrucciones:
                </p>
                <ul>
                  <li>
                    <b>Proveedor de correo electrónico.</b> Cuando pides recuperar tu
                    contraseña, tu dirección de correo y el código de verificación salen por un
                    servidor SMTP de un proveedor externo. Es el único momento en que un dato
                    tuyo sale de la infraestructura del responsable.
                  </li>
                  <li>
                    <b>Proveedor de alojamiento.</b> La base de datos y la aplicación se
                    ejecutan en la infraestructura que contrate el responsable.
                  </li>
                </ul>
                <p>
                  Estas remisiones no requieren tu consentimiento, conforme al artículo 37 de la
                  Ley, por ser necesarias para prestar el servicio que solicitaste.
                </p>

                <h3>7. Cuánto tiempo se conservan</h3>
                <p>
                  Dar de baja a una persona <b>no borra su información</b>: la baja es lógica y
                  el histórico de recibos se conserva, porque la legislación laboral y fiscal
                  obliga a poder acreditar los pagos realizados. Los códigos de recuperación de
                  contraseña caducan y quedan marcados como usados.
                </p>

                <h3>8. Cómo se protegen</h3>
                <p>
                  Las contraseñas no se guardan: se almacena una huella criptográfica de un solo
                  sentido. El acceso a cada dato se verifica en el servidor en cada petición, y
                  las cuentas se bloquean temporalmente tras varios intentos fallidos. Ningún
                  sistema es infalible; si ocurriera una vulneración que afecte de forma
                  significativa tus derechos, se te informará sin dilación.
                </p>

                <h3>9. Tus derechos ARCO</h3>
                <p>
                  Tienes derecho a <b>acceder</b> a tus datos, a <b>rectificarlos</b> si son
                  inexactos, a solicitar su <b>cancelación</b> cuando consideres que no son
                  necesarios, y a <b>oponerte</b> a un tratamiento concreto. También puedes{" "}
                  <b>revocar tu consentimiento</b> y <b>limitar el uso o divulgación</b> de tus
                  datos.
                </p>
                <p>
                  Para ejercerlos, escribe a <b>[CORREO PARA DERECHOS ARCO]</b> indicando tu
                  nombre, un medio para contestarte, los documentos que acrediten tu identidad,
                  la descripción clara de los datos sobre los que ejerces el derecho y qué
                  solicitas exactamente.
                </p>
                <p>
                  La solicitud se responde en un plazo máximo de <b>20 días hábiles</b>, y si
                  procede se hace efectiva dentro de los <b>15 días hábiles</b> siguientes a la
                  respuesta. El ejercicio es gratuito; solo podrían cobrarse los gastos de envío
                  o reproducción.
                </p>
                <p>
                  Ten en cuenta que la cancelación puede no proceder sobre los recibos ya
                  emitidos, por la obligación legal de conservarlos que se describe en el punto
                  7. En ese caso se te explicará el motivo.
                </p>

                <h3>10. Cambios a este aviso</h3>
                <p>
                  Este aviso puede actualizarse. La versión vigente es siempre la publicada en
                  esta página, con su fecha de actualización arriba. Los cambios sustanciales se
                  comunicarán por el correo registrado en el sistema.
                </p>

                <h3>11. Si no estás conforme</h3>
                <p>
                  Si consideras que tu derecho a la protección de datos ha sido vulnerado, puedes
                  acudir al Instituto Nacional de Transparencia, Acceso a la Información y
                  Protección de Datos Personales (INAI).
                </p>
              </div>
            </details>

            <details className="rv-detalle">
              <summary>Términos de uso</summary>
              <div className="rv-detalle-cuerpo">
                <p className="rv-legal-fecha">
                  Última actualización: 14 de septiembre de 2026
                </p>

                <h3>1. Qué es este servicio</h3>
                <p>
                  CEN Payroll calcula las retenciones de ISR e IMSS a partir de un salario bruto
                  y emite un comprobante interno de nómina en PDF. Al usarlo, aceptas estos
                  términos.
                </p>

                <h3>2. Qué no es</h3>
                <p>
                  El comprobante que emite <b>no es un CFDI</b> y no tiene validez fiscal ante el
                  SAT; cada PDF lo lleva impreso. Timbrar un recibo de nómina exige RFC activo,
                  e.firma, Certificado de Sello Digital y contrato con un PAC, y este sistema no
                  hace nada de eso. Si necesitas timbrado, necesitas además otra herramienta.
                </p>
                <p>
                  Tampoco es asesoría fiscal, contable ni laboral, ni sustituye a quien la
                  preste.
                </p>

                <h3>3. Responsabilidad del cálculo</h3>
                <p>
                  Las tarifas de ISR, el subsidio al empleo y las cuotas obrero-patronales del
                  IMSS se aplican tal como están publicadas en el sistema. <b>Quien usa el
                  servicio es responsable</b> de verificar que correspondan al ejercicio vigente
                  y a la situación concreta de cada persona: régimen, prestaciones, incidencias
                  y cualquier concepto que el sistema no contemple.
                </p>

                <h3>4. Acceso y cuentas</h3>
                <p>
                  Las cuentas las crea el administrador de cada organización. No hay registro
                  público. Eres responsable de la confidencialidad de tu contraseña y de lo que
                  ocurra con tu cuenta; el uso de credenciales ajenas está prohibido. Si
                  sospechas un acceso no autorizado, avisa al administrador de inmediato.
                </p>

                <h3>5. Uso permitido</h3>
                <p>
                  El servicio se usa para gestionar la nómina de la propia organización. No está
                  permitido intentar acceder a datos de terceros, interferir con el
                  funcionamiento del sistema, someterlo a pruebas de carga o intrusión sin
                  autorización escrita, ni extraer datos de forma masiva por medios automatizados.
                </p>

                <h3>6. Disponibilidad</h3>
                <p>
                  El servicio se presta <i>tal cual</i>, sin compromiso de disponibilidad
                  ininterrumpida. Puede haber ventanas de mantenimiento, interrupciones por causas
                  ajenas al responsable o cambios en las funciones. Conserva copias de los
                  comprobantes que necesites.
                </p>

                <h3>7. Límite de responsabilidad</h3>
                <p>
                  En la medida que la ley lo permita, el responsable no responde por daños
                  indirectos, lucro cesante ni por decisiones tomadas a partir de un cálculo que
                  no se haya verificado conforme al punto 3. Nada de esto limita la
                  responsabilidad que por ley no pueda excluirse.
                </p>

                <h3>8. Propiedad intelectual</h3>
                <p>
                  El software, su diseño y su documentación pertenecen a sus titulares. Los datos
                  que cargues en el sistema siguen siendo tuyos, o de tu organización.
                </p>

                <h3>9. Terminación</h3>
                <p>
                  El administrador de tu organización puede dar de baja tu cuenta en cualquier
                  momento. La baja es lógica: tu histórico de recibos se conserva por la
                  obligación legal descrita en el aviso de privacidad.
                </p>

                <h3>10. Cambios</h3>
                <p>
                  Estos términos pueden actualizarse. La versión vigente es siempre la publicada
                  en esta página, con su fecha arriba.
                </p>

                <h3>11. Ley aplicable</h3>
                <p>
                  Estos términos se rigen por la legislación de los Estados Unidos Mexicanos.
                  Para cualquier controversia, las partes se someten a los tribunales competentes
                  de <b>[CIUDAD DEL DOMICILIO]</b>, renunciando a cualquier otro fuero.
                </p>
              </div>
            </details>
          </div>
        </section>
      </main>

      <footer className="rv-pie">
        <div className="rv-wrap rv-pie-inner">
          <div className="brand-logo sm">
            <LogoMark />
            <div className="brand-logo-text">
              <span>CEN Payroll</span>
              <small>Sistema de nómina</small>
            </div>
          </div>
          <nav className="rv-pie-links" aria-label="Legal">
            <a href="#legal">Aviso de privacidad</a>
            <a href="#legal">Términos de uso</a>
          </nav>
          <p>© 2026 CEN Payroll. Hecho para equipos de nómina en México.</p>
        </div>
      </footer>
    </div>
  );
}
