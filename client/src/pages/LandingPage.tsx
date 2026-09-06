import { useNavigate } from "react-router-dom";
import { motion } from "motion/react";
import PageTransition from "../components/PageTransition";
import {
  BoltIcon,
  CheckIcon,
  LogoMark,
  ReceiptIcon,
  ShieldIcon,
  UsersIcon,
  WalletIcon
} from "../components/icons";

const trustItems = [
  { label: "Cálculo conforme a ley", value: "ISR + IMSS" },
  { label: "Autenticación segura", value: "JWT" },
  { label: "Acceso por tipo de usuario", value: "RBAC" },
  { label: "Recibos auditables", value: "100%" }
];

const features = [
  {
    eyebrow: "Cálculo automático",
    title: "Sin hojas de cálculo, sin errores manuales",
    description:
      "CEN Payroll calcula ISR e IMSS conforme a la ley mexicana en segundos, para cualquier salario y en cualquier momento del mes.",
    icon: <BoltIcon />
  },
  {
    eyebrow: "Roles y permisos",
    title: "Cada quien ve exactamente lo que le corresponde",
    description:
      "Los administradores dan de alta empleados y calculan nómina; cada empleado entra a su propio panel a consultar sus recibos.",
    icon: <UsersIcon />
  },
  {
    eyebrow: "Recibos al instante",
    title: "Historial de nómina siempre a la mano",
    description:
      "Cada cálculo se guarda como un recibo con desglose completo, disponible de inmediato para el empleado correspondiente.",
    icon: <ReceiptIcon />
  }
];

const securityPoints = [
  "Autenticación segura con tokens JWT",
  "Control de acceso por rol en cada endpoint",
  "Cada recibo generado queda registrado y es auditable"
];

const sectionReveal = {
  initial: { opacity: 0, y: 28 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, amount: 0.3 },
  transition: { duration: 0.5, ease: "easeOut" as const }
};

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <PageTransition>
      <div className="landing-page">
        <header className="landing-nav">
          <div className="landing-nav-inner">
            <div className="brand-logo sm">
              <LogoMark />
              <div className="brand-logo-text">
                <span>CEN Payroll</span>
                <small>Sistema de nómina</small>
              </div>
            </div>
            <nav className="landing-nav-links">
              <a href="#producto">Producto</a>
              <a href="#seguridad">Seguridad</a>
            </nav>
            <div className="landing-nav-actions">
              <button className="landing-btn landing-btn-primary" onClick={() => navigate("/login")}>
                Iniciar sesión
              </button>
            </div>
          </div>
        </header>

        <section className="landing-hero">
          <div className="landing-hero-inner">
            <motion.div
              className="landing-hero-content"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, ease: "easeOut" }}
            >
              <span className="landing-badge">
                <span className="auth-branding-badge-dot" />
                Nómina, reinventada
              </span>
              <h1 className="landing-hero-title">Nómina y mucho más.</h1>
              <p className="landing-hero-subtitle">
                Calcula ISR e IMSS, controla el acceso por rol y entrega recibos auditables a tu
                equipo, todo desde un solo lugar.
              </p>
              <div className="landing-hero-actions">
                <button className="landing-btn landing-btn-primary" onClick={() => navigate("/login")}>
                  Iniciar sesión
                </button>
                <a className="landing-btn landing-btn-ghost" href="#producto">
                  Ver cómo funciona
                </a>
              </div>
              <p className="landing-hero-note">Diseñado para equipos de nómina en México.</p>
            </motion.div>

            <motion.div
              className="landing-hero-visual"
              initial={{ opacity: 0, scale: 0.94 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, ease: "easeOut", delay: 0.15 }}
            >
              <span className="landing-hero-glow" />
              <div className="payroll-result landing-hero-card">
                <p className="payroll-result-heading">Desglose de nómina</p>
                <div className="payroll-result-row">
                  <span>Salario bruto</span>
                  <span>$22,000.00</span>
                </div>
                <div className="payroll-result-row deduction">
                  <span>ISR</span>
                  <span>− $2,800.00</span>
                </div>
                <div className="payroll-result-row deduction">
                  <span>IMSS</span>
                  <span>− $767.90</span>
                </div>
                <div className="payroll-result-row total">
                  <span>Neto a pagar</span>
                  <span>$18,432.10</span>
                </div>
              </div>

              <motion.div
                className="landing-hero-chip"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, ease: "easeOut", delay: 0.5 }}
              >
                <span className="landing-hero-chip-icon">
                  <ReceiptIcon />
                </span>
                <div>
                  <p className="landing-hero-chip-label">Recibo generado</p>
                  <p className="landing-hero-chip-value">+$18,432.10</p>
                </div>
              </motion.div>
            </motion.div>
          </div>
        </section>

        <motion.section className="trust-bar" {...sectionReveal}>
          {trustItems.map((item) => (
            <div className="trust-item" key={item.label}>
              <p className="trust-item-value">{item.value}</p>
              <p className="trust-item-label">{item.label}</p>
            </div>
          ))}
        </motion.section>

        <section id="producto" className="feature-section">
          {features.map((feature, index) => (
            <motion.div
              className={`feature-row${index % 2 === 1 ? " reverse" : ""}`}
              key={feature.title}
              {...sectionReveal}
            >
              <div className="feature-copy">
                <span className="feature-eyebrow">{feature.eyebrow}</span>
                <h2 className="feature-title">{feature.title}</h2>
                <p className="feature-description">{feature.description}</p>
              </div>
              <div className="feature-visual">
                <span className="feature-visual-icon">{feature.icon}</span>
              </div>
            </motion.div>
          ))}
        </section>

        <motion.section id="seguridad" className="security-section" {...sectionReveal}>
          <div className="security-grid">
            <div>
              <span className="feature-eyebrow">Seguridad</span>
              <h2 className="feature-title">Tu nómina, protegida</h2>
              <p className="feature-description">
                La información sensible de tu equipo se resguarda con autenticación robusta y
                control de acceso en cada capa de la plataforma.
              </p>
              <ul className="security-list">
                {securityPoints.map((point) => (
                  <li className="security-list-item" key={point}>
                    <span className="security-list-icon">
                      <CheckIcon />
                    </span>
                    {point}
                  </li>
                ))}
              </ul>
            </div>
            <div className="security-visual">
              <span className="security-visual-icon">
                <ShieldIcon />
              </span>
            </div>
          </div>
        </motion.section>

        <motion.section className="cta-banner" {...sectionReveal}>
          <span className="cta-banner-icon">
            <WalletIcon />
          </span>
          <h2 className="cta-banner-title">Lleva la nómina de tu equipo al siguiente nivel</h2>
          <p className="cta-banner-subtitle">
            Inicia sesión para calcular nómina, dar de alta empleados o consultar tus recibos.
          </p>
          <button className="landing-btn landing-btn-primary" onClick={() => navigate("/login")}>
            Iniciar sesión
          </button>
        </motion.section>

        <footer className="landing-footer">
          <div className="brand-logo sm">
            <LogoMark />
            <div className="brand-logo-text">
              <span>CEN Payroll</span>
              <small>Sistema de nómina</small>
            </div>
          </div>
          <p className="landing-footer-copy">© 2026 CEN Payroll. Todos los derechos reservados.</p>
        </footer>
      </div>
    </PageTransition>
  );
}
