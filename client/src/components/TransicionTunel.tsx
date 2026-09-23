import { ReactNode, useCallback, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion, type TargetAndTransition } from "motion/react";
import { LogoMark } from "./icons";
import { EASE_TUNEL } from "../motion/variants";
import { TunelContext, type PasarPorTunel } from "../motion/tunel";

// Tiempos del tunel, en segundos: tapar con el logo, navegar por debajo y atravesarlo.
const TUNEL = {
  velo: 0.3,
  viaje: 0.45,
  zoom: 0.6,
  destape: 0.2
} as const;

// Criticamente amortiguado: un clic no trae impulso, asi que nada rebota.
const SPRING = { type: "spring", bounce: 0 } as const;

const VELO_OPACO = { opacity: 1, backdropFilter: "blur(20px)" };
const VELO_ABIERTO = { opacity: 0, backdropFilter: "blur(0px)" };

type Fase = "quieto" | "tapando" | "zoom";

function ladoDelLogo() {
  return window.matchMedia("(max-width: 480px)").matches ? 72 : 96;
}

// Donde arranca el logo: sobre el elemento que disparo el salto, a su escala.
function salidaDesde(origen: Element | null | undefined, compartido: boolean): TargetAndTransition {
  const caja = origen?.getBoundingClientRect();
  if (!caja || caja.width === 0) return { x: 0, y: 0, scale: 0.6, opacity: 0 };

  return {
    x: caja.left + caja.width / 2 - window.innerWidth / 2,
    y: caja.top + caja.height / 2 - window.innerHeight / 2,
    scale: Math.min(caja.width, caja.height) / ladoDelLogo(),
    opacity: compartido ? 1 : 0
  };
}

// Para los saltos grandes (entrar al panel, cerrar sesion): el resto de rutas se queda con el fade corto.
export function TunelProvider({ children }: { children: ReactNode }) {
  const reduceMotion = useReducedMotion();
  const [fase, setFase] = useState<Fase>("quieto");
  const [inicio, setInicio] = useState<TargetAndTransition>({});
  const pendiente = useRef<(() => void) | null>(null);

  const pasar = useCallback<PasarPorTunel>(
    (navegar, opciones) => {
      if (reduceMotion) {
        navegar();
        return;
      }
      if (pendiente.current) return;
      pendiente.current = navegar;
      setInicio(salidaDesde(opciones?.origen, opciones?.compartido ?? false));
      setFase("tapando");
    },
    [reduceMotion]
  );

  function alTerminarLogo() {
    if (fase === "tapando") {
      const navegar = pendiente.current;
      pendiente.current = null;
      navegar?.();
      setFase("zoom");
    } else if (fase === "zoom") {
      setFase("quieto");
    }
  }

  return (
    <TunelContext.Provider value={pasar}>
      {children}
      <AnimatePresence>
        {fase !== "quieto" && (
          <motion.div key="tunel" className="app-tunel" aria-hidden="true">
            {/* El fondo se materializa (desenfoque y opacidad juntos) en vez de solo aparecer. */}
            <motion.div
              className="app-tunel-velo"
              initial={VELO_ABIERTO}
              animate={VELO_OPACO}
              exit={{ ...VELO_ABIERTO, transition: { duration: TUNEL.destape } }}
              transition={{ duration: TUNEL.velo }}
            />
            <motion.div
              className="app-tunel-logo"
              initial={inicio}
              animate={
                fase === "zoom"
                  ? { x: 0, y: 0, scale: 24, opacity: 0 }
                  : { x: 0, y: 0, scale: 1, opacity: 1 }
              }
              transition={
                fase === "zoom"
                  ? {
                      scale: { duration: TUNEL.zoom, ease: EASE_TUNEL },
                      opacity: { delay: TUNEL.zoom * 0.7, duration: TUNEL.zoom * 0.3 }
                    }
                  : {
                      x: { ...SPRING, duration: TUNEL.viaje },
                      y: { ...SPRING, duration: TUNEL.viaje },
                      scale: { ...SPRING, duration: TUNEL.viaje },
                      opacity: { duration: TUNEL.viaje * 0.5 }
                    }
              }
              onAnimationComplete={alTerminarLogo}
            >
              <LogoMark />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </TunelContext.Provider>
  );
}
