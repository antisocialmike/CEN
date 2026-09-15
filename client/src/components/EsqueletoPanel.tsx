import Skeleton from "./Skeleton";

export default function EsqueletoPanel() {
  return (
    <>
      <p className="visually-hidden" role="status">
        Cargando tu panel
      </p>

      <div className="dashboard-panel" aria-hidden="true">
        <div className="dashboard-panel-header">
          <div className="skeleton-stack" style={{ flex: 1 }}>
            <Skeleton width="38%" height={20} />
            <Skeleton width="60%" height={12} />
          </div>
        </div>

        <div className="stat-row">
          {[0, 1, 2].map((indice) => (
            <div className="stat-card" key={indice}>
              <Skeleton width="36px" height={36} />
              <div className="skeleton-stack" style={{ flex: 1 }}>
                <Skeleton width="70%" height={11} />
                <Skeleton width="50%" height={16} />
              </div>
            </div>
          ))}
        </div>

        <div className="skeleton-card skeleton-stack">
          <Skeleton width="45%" height={16} />
          <Skeleton height={14} />
          <Skeleton height={14} />
          <Skeleton width="60%" height={14} />
        </div>
      </div>
    </>
  );
}
