import { useEffect, useRef, useState } from "react";
import {
  animate,
  motion,
  useMotionValue,
  useMotionValueEvent,
  useReducedMotion
} from "motion/react";
import { EASE_OUT } from "../motion/variants";

// Todas las marcas de tiempo del splash, en segundos, para afinar desde un solo sitio.
const TIMELINE = {
  reticula: 0.05,
  guias: 0.15,
  trazo: { inicio: 0.4, duracion: 1.05 },
  barras: { inicio: 0.75, duracion: 0.6 },
  relleno: { inicio: 1.5, duracion: 0.45 },
  rebote: 1.9,
  marca: 2.1,
  letras: 0.028,
  linea: 2.55,
  lema: 2.7,
  finIntro: 3.0,
  salida: { texto: 0.15, zoom: 0.6, fondo: 0.2 },
  breve: { fade: 0.2, minimo: 0.6 }
} as const;

const EASE_TRAZO = [0.65, 0, 0.35, 1] as const;
const EASE_ZOOM = [0.7, 0, 0.84, 0] as const;

// La misma geometria que LogoMark, con las barras pasadas a path para poder trazarlas.
const CONTORNO = "M4.5 4H27.5V7.6H8.1V24.4H27.5V28H4.5Z";
const BARRAS = ["M12 11.7H27.5V15.1H12Z", "M12 18.1H27.5V21.5H12Z"];

// Vertices del contorno con la fraccion del recorrido en la que el trazo pasa por cada uno.
const NODOS_CONTORNO = [
  { x: 4.5, y: 4, en: 0 },
  { x: 27.5, y: 4, en: 0.173 },
  { x: 27.5, y: 7.6, en: 0.2 },
  { x: 8.1, y: 7.6, en: 0.346 },
  { x: 8.1, y: 24.4, en: 0.473 },
  { x: 27.5, y: 24.4, en: 0.619 },
  { x: 27.5, y: 28, en: 0.646 },
  { x: 4.5, y: 28, en: 0.819 }
];

const NODOS_BARRAS = [
  [12, 11.7], [27.5, 11.7], [27.5, 15.1], [12, 15.1],
  [12, 18.1], [27.5, 18.1], [27.5, 21.5], [12, 21.5]
];

const GUIAS = [
  { x1: -24, y1: 0, x2: 56, y2: 0, grad: "h" },
  { x1: -24, y1: 32, x2: 56, y2: 32, grad: "h" },
  { x1: 0, y1: -24, x2: 0, y2: 56, grad: "v" },
  { x1: 32, y1: -24, x2: 32, y2: 56, grad: "v" }
];

const NOMBRE = [
  { texto: "CEN", acento: false },
  { texto: " ", acento: false },
  { texto: "Payroll", acento: true }
];

type AppLoaderProps = {
  // Sin intro es el fallback de una carga en caliente: logo quieto y un fade.
  intro?: boolean;
  listo?: boolean;
  alTerminar?: () => void;
};

function LogoSolido() {
  return (
    <>
      <rect width="32" height="32" fill="var(--rosa)" />
      <path d={CONTORNO} fill="#fff" />
      {BARRAS.map((d) => (
        <path key={d} d={d} fill="#fff" />
      ))}
    </>
  );
}

type NodoProps = { x: number; y: number; visible: boolean; clase: string; retraso?: number };

function Nodo({ x, y, visible, clase, retraso = 0 }: NodoProps) {
  return (
    <motion.rect
      className={clase}
      x={x - 0.6}
      y={y - 0.6}
      width={1.2}
      height={1.2}
      initial={{ scale: 0, opacity: 0 }}
      animate={visible ? { scale: 1, opacity: 1 } : { scale: 0, opacity: 0 }}
      transition={{ type: "spring", duration: 0.35, bounce: 0.35, delay: retraso }}
    />
  );
}

function Blueprint() {
  const trazo = useRef<SVGPathElement>(null);
  const progreso = useMotionValue(0);
  const puntaX = useMotionValue(NODOS_CONTORNO[0].x);
  const puntaY = useMotionValue(NODOS_CONTORNO[0].y);
  const [nodosVisibles, setNodosVisibles] = useState(0);
  const [barrasVisibles, setBarrasVisibles] = useState(false);

  useMotionValueEvent(progreso, "change", (v) => {
    const path = trazo.current;
    if (path && typeof path.getTotalLength === "function") {
      const punto = path.getPointAtLength(v * path.getTotalLength());
      puntaX.set(punto.x);
      puntaY.set(punto.y);
    }
    const n = NODOS_CONTORNO.filter((nodo) => nodo.en <= v + 0.001).length;
    setNodosVisibles((previo) => (previo === n ? previo : n));
  });

  useEffect(() => {
    const { inicio, duracion } = TIMELINE.trazo;
    const controles = animate(progreso, 1, { delay: inicio, duration: duracion, ease: EASE_TRAZO });
    const barras = window.setTimeout(() => setBarrasVisibles(true), TIMELINE.barras.inicio * 1000);
    return () => {
      controles.stop();
      window.clearTimeout(barras);
    };
  }, [progreso]);

  const { inicio: inicioRelleno, duracion: duracionRelleno } = TIMELINE.relleno;

  return (
    <motion.svg
      className="app-loader-blueprint"
      viewBox="0 0 32 32"
      initial={{ opacity: 1 }}
      animate={{ opacity: 0 }}
      transition={{ delay: inicioRelleno + duracionRelleno * 0.55, duration: 0.2 }}
    >
      <defs>
        <linearGradient id="app-loader-guia-h" x1="-24" y1="0" x2="56" y2="0" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="currentColor" stopOpacity="0" />
          <stop offset="0.35" stopColor="currentColor" />
          <stop offset="0.65" stopColor="currentColor" />
          <stop offset="1" stopColor="currentColor" stopOpacity="0" />
        </linearGradient>
        <linearGradient id="app-loader-guia-v" x1="0" y1="-24" x2="0" y2="56" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="currentColor" stopOpacity="0" />
          <stop offset="0.35" stopColor="currentColor" />
          <stop offset="0.65" stopColor="currentColor" />
          <stop offset="1" stopColor="currentColor" stopOpacity="0" />
        </linearGradient>
      </defs>

      <g className="app-loader-guias">
        {GUIAS.map((g, i) => (
          <motion.line
            key={i}
            x1={g.x1}
            y1={g.y1}
            x2={g.x2}
            y2={g.y2}
            stroke={`url(#app-loader-guia-${g.grad})`}
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ delay: TIMELINE.guias + i * 0.06, duration: 0.6, ease: EASE_OUT }}
          />
        ))}
      </g>

      <motion.path ref={trazo} className="app-loader-trazo" d={CONTORNO} style={{ pathLength: progreso }} />

      {BARRAS.map((d, i) => (
        <motion.path
          key={d}
          className="app-loader-trazo is-barra"
          d={d}
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{
            delay: TIMELINE.barras.inicio + i * 0.12,
            duration: TIMELINE.barras.duracion,
            ease: EASE_TRAZO
          }}
        />
      ))}

      {NODOS_CONTORNO.map((n, i) => (
        <Nodo key={i} x={n.x} y={n.y} visible={i < nodosVisibles} clase="app-loader-nodo" />
      ))}
      {NODOS_BARRAS.map(([x, y], i) => (
        <Nodo
          key={i}
          x={x}
          y={y}
          visible={barrasVisibles}
          clase="app-loader-nodo is-barra"
          retraso={i * 0.05}
        />
      ))}

      <motion.g
        initial={{ opacity: 0 }}
        animate={{ opacity: [0, 1, 1, 0] }}
        transition={{
          delay: TIMELINE.trazo.inicio,
          duration: TIMELINE.trazo.duracion + 0.15,
          times: [0, 0.05, 0.9, 1]
        }}
      >
        <motion.circle className="app-loader-halo" r={1.8} cx={puntaX} cy={puntaY} />
        <motion.circle className="app-loader-punta" r={0.45} cx={puntaX} cy={puntaY} />
      </motion.g>
    </motion.svg>
  );
}

export default function AppLoader({ intro = true, listo = false, alTerminar }: AppLoaderProps) {
  const reduceMotion = useReducedMotion();
  const conIntro = intro && !reduceMotion;
  const [introTerminada, setIntroTerminada] = useState(false);
  const terminado = useRef(false);

  useEffect(() => {
    const espera = conIntro ? TIMELINE.finIntro : TIMELINE.breve.minimo;
    const temporizador = window.setTimeout(() => setIntroTerminada(true), espera * 1000);
    return () => window.clearTimeout(temporizador);
  }, [conIntro]);

  const saliendo = listo && introTerminada;
  const { salida } = TIMELINE;

  const avisarFin = () => {
    if (!saliendo || terminado.current) return;
    terminado.current = true;
    alTerminar?.();
  };

  // Retraso de cada pieza del nombre: sin intro todo entra junto con el fade.
  const retraso = (segundos: number) => (conIntro ? segundos : 0);
  const entrada = conIntro ? 0.35 : TIMELINE.breve.fade;

  let letra = 0;

  return (
    <motion.div
      className="app-loader"
      role="status"
      aria-live="polite"
      initial={{ opacity: conIntro ? 1 : 0 }}
      animate={{ opacity: saliendo ? 0 : 1 }}
      transition={
        saliendo
          ? { delay: conIntro ? salida.zoom - 0.1 : 0, duration: salida.fondo }
          : { duration: TIMELINE.breve.fade }
      }
      onAnimationComplete={avisarFin}
    >
      <span className="visually-hidden">Cargando CEN Payroll…</span>

      <motion.div
        className="app-loader-reticula"
        aria-hidden="true"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: retraso(TIMELINE.reticula), duration: 0.6 }}
      />

      <div className="app-loader-escena" aria-hidden="true">
        <motion.div
          className="app-loader-capa"
          initial={conIntro ? { y: "0%", scale: 1 } : false}
          animate={{ y: "-30%", scale: 0.72 }}
          transition={{ delay: retraso(TIMELINE.marca), type: "spring", duration: conIntro ? 0.7 : 0, bounce: 0.15 }}
        >
          <motion.div
            className="app-loader-capa"
            animate={saliendo && conIntro ? { scale: 24, opacity: 0 } : { scale: 1, opacity: 1 }}
            transition={{
              scale: { duration: salida.zoom, ease: EASE_ZOOM },
              opacity: { delay: salida.zoom * 0.7, duration: salida.zoom * 0.3 }
            }}
          >
            <motion.div
              className="app-loader-capa"
              animate={conIntro ? { scale: [1, 1.015, 1] } : undefined}
              transition={{ delay: TIMELINE.finIntro, duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
            >
              <motion.div
                className="app-loader-mark"
                initial={false}
                animate={conIntro ? { scale: [1, 1.04, 1] } : undefined}
                transition={{ delay: TIMELINE.rebote, duration: 0.45, ease: EASE_OUT }}
              >
                {conIntro && <Blueprint />}
                <motion.svg
                  className="app-loader-relleno"
                  viewBox="0 0 32 32"
                  initial={{
                    clipPath: conIntro
                      ? "polygon(100% 0%, 100% 0%, 100% 0%)"
                      : "polygon(100% 0%, -120% 0%, 100% 220%)"
                  }}
                  animate={{ clipPath: "polygon(100% 0%, -120% 0%, 100% 220%)" }}
                  transition={{
                    delay: TIMELINE.relleno.inicio,
                    duration: TIMELINE.relleno.duracion,
                    ease: EASE_OUT
                  }}
                >
                  <LogoSolido />
                </motion.svg>
              </motion.div>
            </motion.div>
          </motion.div>
        </motion.div>

        <motion.div
          className="app-loader-textos"
          animate={{ opacity: saliendo ? 0 : 1 }}
          transition={{ duration: salida.texto }}
        >
          <p className="app-loader-nombre">
            {NOMBRE.map((parte) => (
              <span key={parte.texto} className={parte.acento ? "is-acento" : undefined}>
                {Array.from(parte.texto).map((caracter, i) => {
                  const orden = letra++;
                  return (
                    <motion.span
                      key={i}
                      className="app-loader-letra"
                      initial={{ opacity: 0, y: conIntro ? 6 : 0, filter: conIntro ? "blur(4px)" : "blur(0px)" }}
                      animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                      transition={{
                        delay: retraso(TIMELINE.marca + 0.15 + orden * TIMELINE.letras),
                        duration: entrada,
                        ease: EASE_OUT
                      }}
                    >
                      {caracter}
                    </motion.span>
                  );
                })}
              </span>
            ))}
          </p>
          <motion.span
            className="app-loader-linea"
            initial={{ scaleX: conIntro ? 0 : 1 }}
            animate={{ scaleX: 1 }}
            transition={{ delay: retraso(TIMELINE.linea), duration: 0.4, ease: EASE_OUT }}
          />
          <motion.p
            className="app-loader-lema"
            initial={{ opacity: 0, y: conIntro ? 4 : 0 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: retraso(TIMELINE.lema), duration: entrada, ease: EASE_OUT }}
          >
            Nómina que cuadra.
          </motion.p>
        </motion.div>
      </div>
    </motion.div>
  );
}
