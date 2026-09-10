import { Link, useNavigate } from "react-router-dom";
import { motion, useReducedMotion } from "motion/react";
import {
  ArrowRight,
  Check,
  Database,
  Key,
  Receipt,
  ShieldCheck,
  UsersThree
} from "@phosphor-icons/react";
import { LogoMark } from "../components/icons";
import ThemeToggle from "../components/ThemeToggle";


const calculo = [
  { label: "Salario bruto", value: "$22,000.00" },
  { label: "ISR retenido", value: "− $2,800.00" },
  { label: "IMSS retenido", value: "− $767.90" },
  { label: "Neto a pagar", value: "$18,432.10", net: true }
];

const recibos = [
  { mes: "Agosto 2026", folio: "128", neto: "$18,432.10", bruto: "$22,000.00", isr: "$2,800.00", imss: "$767.90" },
  { mes: "Julio 2026", folio: "111", neto: "$18,432.10", bruto: "$22,000.00", isr: "$2,800.00", imss: "$767.90" },
  { mes: "Junio 2026", folio: "94", neto: "$17,658.40", bruto: "$21,000.00", isr: "$2,610.40", imss: "$731.20" },
  { mes: "Mayo 2026", folio: "77", neto: "$17,658.40", bruto: "$21,000.00", isr: "$2,610.40", imss: "$731.20" }
];

const flujo = [
  { icon: <Key weight="bold" />, text: <>La petición llega con su <b>token JWT</b></> },
  { icon: <ShieldCheck weight="bold" />, text: <>El servidor verifica <b>firma y caducidad</b></> },
  { icon: <UsersThree weight="bold" />, text: <>Comprueba el <b>rol que exige el endpoint</b></> },
  { icon: <Database weight="bold" />, text: <>Solo entonces, <b>acceso a los datos</b></>, end: true }
];

export default function LandingPage() {
  const navigate = useNavigate();
  const reduce = useReducedMotion();

  const wipe = (delay: number) =>
    reduce
      ? {}
      : {
          initial: { clipPath: "inset(0 100% 0 0)" },
          animate: { clipPath: "inset(0 0% 0 0)" },
          transition: { duration: 0.7, ease: [0.22, 1, 0.36, 1] as const, delay }
        };

  const rise = {
    initial: reduce ? false : { opacity: 0, y: 20 },
    whileInView: { opacity: 1, y: 0 },
    viewport: { once: true, amount: 0.3 },
    transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] as const }
  };

  return (
    <div className="lp">
      <a className="skip-link" href="#calculo">
        Ir al contenido
      </a>

      <header className="lp-nav">
        <div className="lp-wrap lp-nav-inner">
          <Link className="brand-logo" to="/">
            <LogoMark />
            <div className="brand-logo-text">
              <span>CEN Payroll</span>
              <small>Sistema de nómina</small>
            </div>
          </Link>
          <nav className="lp-nav-links" aria-label="Secciones">
            <a href="#calculo">El cálculo</a>
            <a href="#roles">Roles</a>
            <a href="#seguridad">Seguridad</a>
          </nav>
          <ThemeToggle />
          <button className="btn btn-rosa" onClick={() => navigate("/login")}>
            Iniciar sesión
          </button>
        </div>
      </header>

      <main>
        <section className="lp-hero">
          <div className="lp-wrap lp-hero-grid">
            <motion.div
              className="lp-hero-copy"
              initial={reduce ? false : { opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
            >
              <h1 className="lp-hero-title">Nómina que cuadra.</h1>
              <p className="lp-hero-sub">
                Calculas el bruto, CEN devuelve el ISR, el IMSS y el neto. Cada recibo queda
                guardado.
              </p>
              <div className="lp-hero-actions">
                <button className="btn btn-rosa" onClick={() => navigate("/login")}>
                  Iniciar sesión
                  <ArrowRight weight="bold" />
                </button>
                <a className="btn btn-line" href="#calculo">
                  Ver cómo funciona
                </a>
              </div>
            </motion.div>

            <div className="lp-stage">
              <motion.span className="lp-plane lp-plane-ocre" aria-hidden="true" {...wipe(0.1)} />
              <motion.span className="lp-plane lp-plane-rosa" aria-hidden="true" {...wipe(0.22)} />

              <motion.div
                className="lp-deposit"
                initial={reduce ? false : { opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1], delay: 0.95 }}
              >
                <span className="lp-deposit-mark" aria-hidden="true">
                  <Receipt weight="bold" />
                </span>
                <div>
                  <p className="lp-deposit-label">Recibo emitido</p>
                  <p className="lp-deposit-value">$18,432.10</p>
                </div>
              </motion.div>
            </div>
          </div>
        </section>

        <section className="lp-calc" id="calculo">
          <div className="lp-wrap">
            <h2 className="lp-calc-title">Una quincena de $22,000, desglosada</h2>
            <div className="lp-calc-row">
              {calculo.map((paso, i) => (
                <motion.div
                  className={`lp-calc-cell${paso.net ? " is-net" : ""}`}
                  key={paso.label}
                  initial={reduce ? false : { opacity: 0, y: 14 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, amount: 0.5 }}
                  transition={{
                    duration: 0.45,
                    ease: [0.22, 1, 0.36, 1],
                    delay: reduce ? 0 : i * 0.11
                  }}
                >
                  <span className="lp-calc-label">{paso.label}</span>
                  <span className="lp-calc-fig">{paso.value}</span>
                </motion.div>
              ))}
            </div>
            <p className="lp-calc-note">
              El ISR y el IMSS salen de las tablas vigentes, no de un porcentaje fijo. La misma
              fórmula para todo tu equipo, todos los periodos.
            </p>
          </div>
        </section>

        <section className="lp-roles" id="roles">
          <div className="lp-wrap">
            <div className="lp-roles-head">
              <h2>Cada quien entra a lo suyo.</h2>
            </div>
            <div className="lp-roles-grid">
              <motion.article className="lp-role lp-role--admin" {...rise}>
                <div className="lp-role-body">
                  <h3>Administrador</h3>
                  <p>Da de alta al equipo, calcula la nómina y ve los recibos de todos.</p>
                  <ul className="lp-role-list">
                    <li>
                      <Check weight="bold" />
                      Alta de empleados con salario base
                    </li>
                    <li>
                      <Check weight="bold" />
                      Cálculo de ISR e IMSS por periodo
                    </li>
                    <li>
                      <Check weight="bold" />
                      Historial completo del equipo
                    </li>
                  </ul>
                </div>
              </motion.article>

              <motion.article
                className="lp-role lp-role--empleado"
                {...rise}
                transition={{ ...rise.transition, delay: reduce ? 0 : 0.1 }}
              >
                <div className="lp-role-body">
                  <h3>Empleado</h3>
                  <p>Entra a su propio portal y encuentra sus recibos. Nada más, nada menos.</p>
                  <ul className="lp-role-list">
                    <li>
                      <Check weight="bold" />
                      Sus recibos, desde el primero
                    </li>
                    <li>
                      <Check weight="bold" />
                      Desglose de lo que se retuvo
                    </li>
                    <li>
                      <Check weight="bold" />
                      Sin pedirlo por correo
                    </li>
                  </ul>
                </div>
              </motion.article>
            </div>
          </div>
        </section>

        <section className="lp-rail-section">
          <div className="lp-wrap">
            <div className="lp-rail-head">
              <h2>El historial no se pierde.</h2>
              <p>
                Cada cálculo se guarda con su folio y su fecha. El empleado lo tiene al instante.
              </p>
            </div>
          </div>
          <div className="lp-wrap">
            <div className="lp-rail" tabIndex={0} role="group" aria-label="Recibos de ejemplo">
              {recibos.map((r) => (
                <article className="lp-receipt" key={r.folio}>
                  <div className="lp-receipt-top">
                    <span className="lp-receipt-month">{r.mes}</span>
                    <span className="lp-receipt-folio">#{r.folio}</span>
                  </div>
                  <div>
                    <p className="lp-receipt-net-label">Neto</p>
                    <p className="lp-receipt-net">{r.neto}</p>
                  </div>
                  <div className="lp-receipt-lines">
                    <span className="lp-receipt-line">
                      Bruto <b>{r.bruto}</b>
                    </span>
                    <span className="lp-receipt-line">
                      ISR <b>− {r.isr}</b>
                    </span>
                    <span className="lp-receipt-line">
                      IMSS <b>− {r.imss}</b>
                    </span>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="lp-sec" id="seguridad">
          <div className="lp-wrap lp-sec-grid">
            <div>
              <h2>El sueldo de tu equipo no es dato público.</h2>
              <p className="lp-sec-lead">
                El permiso se verifica en el servidor, nunca en la interfaz. Un empleado no puede
                pedir los recibos de otro aunque escriba la dirección a mano.
              </p>
            </div>
            <div className="lp-flow">
              {flujo.map((paso, i) => (
                <div className={`lp-flow-step${paso.end ? " is-end" : ""}`} key={i}>
                  <span aria-hidden="true">{paso.icon}</span>
                  <span>{paso.text}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="lp-cta">
          <div className="lp-wrap lp-cta">
            <h2>Tu próxima nómina, en dos minutos.</h2>
            <p>Entra para calcular la nómina de tu equipo o para consultar tus recibos.</p>
            <button className="btn btn-rosa" onClick={() => navigate("/login")}>
              Iniciar sesión
              <ArrowRight weight="bold" />
            </button>
          </div>
        </section>
      </main>

      <footer className="lp-wrap lp-foot">
        <div className="brand-logo sm">
          <LogoMark />
          <div className="brand-logo-text">
            <span>CEN Payroll</span>
            <small>Sistema de nómina</small>
          </div>
        </div>
        <p>© 2026 CEN Payroll. Hecho para equipos de nómina en México.</p>
      </footer>
    </div>
  );
}
