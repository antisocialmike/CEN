from typing import Optional

from psycopg2.extras import Json

from ..config.database import db_cursor

OWNER_FIELDS = (
    "SELECT e.id, e.name, e.email, e.is_active, "
    "COALESCE(json_agg(json_build_object("
    "'id', c.id, 'legal_name', c.legal_name, 'is_active', c.is_active) "
    "ORDER BY c.legal_name) FILTER (WHERE c.id IS NOT NULL), '[]') "
    "AS companies "
    "FROM employees e "
    "LEFT JOIN company_owners o ON o.owner_id = e.id "
    "LEFT JOIN companies c ON c.id = o.company_id "
)
SELECT_OWNERS = (
    OWNER_FIELDS
    + "WHERE e.role = 'owner' GROUP BY e.id "
    "ORDER BY e.is_active DESC, e.name ASC;"
)
SELECT_OWNER = (
    OWNER_FIELDS + "WHERE e.id = %s AND e.role = 'owner' GROUP BY e.id;"
)
INSERT_OWNER = (
    "INSERT INTO employees (name, email, role, base_salary, password_hash, "
    "must_change_password) VALUES (%s, %s, 'owner', NULL, %s, TRUE) "
    "RETURNING id;"
)
UPDATE_OWNER = (
    "UPDATE employees SET name = %s, email = %s "
    "WHERE id = %s AND role = 'owner' RETURNING id;"
)
UPDATE_OWNER_ACTIVE = (
    "UPDATE employees SET is_active = %s "
    "WHERE id = %s AND role = 'owner' RETURNING id;"
)
RESET_OWNER_PASSWORD = (
    "UPDATE employees SET password_hash = %s, must_change_password = TRUE, "
    "failed_login_attempts = 0, locked_until = NULL "
    "WHERE id = %s AND role = 'owner' RETURNING id, name, email;"
)
LOCK_ACTIVE_OWNER = (
    "SELECT id FROM employees "
    "WHERE id = %s AND role = 'owner' AND is_active FOR SHARE;"
)
# Empresas activas que se quedarian sin ningun dueno activo si el dueno
# indicado dejara de contar. Bloquea esas empresas hasta el fin de la
# transaccion para que dos bajas simultaneas no dejen una huerfana.
SELECT_COMPANIES_LEFT_WITHOUT_OWNER = (
    "SELECT c.id, c.legal_name FROM companies c "
    "JOIN company_owners o ON o.company_id = c.id "
    "WHERE o.owner_id = %s AND c.is_active AND (%s IS NULL OR c.id = %s) "
    "AND NOT EXISTS ("
    "SELECT 1 FROM company_owners other "
    "JOIN employees e ON e.id = other.owner_id "
    "WHERE other.company_id = c.id AND other.owner_id <> %s AND e.is_active"
    ") ORDER BY c.id FOR UPDATE OF c;"
)

COMPANY_FIELDS = (
    "SELECT c.id, c.legal_name, c.trade_name, c.rfc, c.registro_patronal, "
    "c.entidad_federativa, c.is_active, c.created_at, "
    "COALESCE(json_agg(json_build_object("
    "'id', e.id, 'name', e.name, 'is_active', e.is_active) "
    "ORDER BY e.name) FILTER (WHERE e.id IS NOT NULL), '[]') AS owners "
    "FROM companies c "
    "LEFT JOIN company_owners o ON o.company_id = c.id "
    "LEFT JOIN employees e ON e.id = o.owner_id "
)
SELECT_COMPANIES = (
    COMPANY_FIELDS
    + "GROUP BY c.id ORDER BY c.is_active DESC, c.legal_name ASC;"
)
SELECT_COMPANY = COMPANY_FIELDS + "WHERE c.id = %s GROUP BY c.id;"
INSERT_COMPANY = (
    "INSERT INTO companies (legal_name, trade_name, rfc, registro_patronal, "
    "entidad_federativa) VALUES (%s, %s, %s, %s, %s) RETURNING id;"
)
UPDATE_COMPANY = (
    "UPDATE companies SET legal_name = %s, trade_name = %s, rfc = %s, "
    "registro_patronal = %s, entidad_federativa = %s "
    "WHERE id = %s RETURNING id;"
)
LOCK_COMPANY = "SELECT id FROM companies WHERE id = %s FOR UPDATE;"
INSERT_COMPANY_OWNER = (
    "INSERT INTO company_owners (owner_id, company_id) VALUES (%s, %s) "
    "ON CONFLICT (owner_id, company_id) DO NOTHING RETURNING owner_id;"
)
DELETE_COMPANY_OWNER = (
    "DELETE FROM company_owners WHERE owner_id = %s AND company_id = %s "
    "RETURNING owner_id;"
)
SELECT_ADMIN_COMPANY_IDS = (
    "SELECT ca.company_id FROM company_admins ca "
    "JOIN companies c ON c.id = ca.company_id "
    "WHERE ca.admin_id = %s AND ca.is_active AND c.is_active "
    "ORDER BY c.legal_name;"
)
SELECT_ADMIN_COMPANY = (
    "SELECT ca.company_id FROM company_admins ca "
    "JOIN companies c ON c.id = ca.company_id "
    "WHERE ca.admin_id = %s AND ca.company_id = %s "
    "AND ca.is_active AND c.is_active;"
)
SELECT_OWNER_COMPANY = (
    "SELECT company_id FROM company_owners "
    "WHERE owner_id = %s AND company_id = %s;"
)
OWNER_COMPANY_FIELDS = (
    "SELECT c.id, c.legal_name, c.trade_name, c.rfc, c.registro_patronal, "
    "c.entidad_federativa, c.is_active, c.created_at, "
    "COALESCE(json_agg(json_build_object("
    "'id', e.id, 'name', e.name, 'email', e.email, "
    "'is_active', e.is_active, 'assigned_at', ca.created_at) "
    "ORDER BY e.name) FILTER (WHERE e.id IS NOT NULL), '[]') AS admins "
    "FROM companies c "
    "JOIN company_owners o ON o.company_id = c.id AND o.owner_id = %s "
    "LEFT JOIN company_admins ca ON ca.company_id = c.id AND ca.is_active "
    "LEFT JOIN employees e ON e.id = ca.admin_id "
)
SELECT_OWNER_COMPANIES = (
    OWNER_COMPANY_FIELDS
    + "GROUP BY c.id ORDER BY c.is_active DESC, c.legal_name ASC;"
)
SELECT_OWNER_COMPANY_DETAIL = (
    OWNER_COMPANY_FIELDS + "WHERE c.id = %s GROUP BY c.id;"
)
UPDATE_COMPANY_ACTIVE = (
    "UPDATE companies SET is_active = %s WHERE id = %s RETURNING id;"
)
INSERT_ADMIN = (
    "INSERT INTO employees (name, email, role, base_salary, password_hash, "
    "must_change_password) VALUES (%s, %s, 'admin', NULL, %s, TRUE) "
    "RETURNING id;"
)
# Solo se busca un admin activo por su correo exacto: el dueno no puede
# listar ni adivinar a los admins de otras empresas.
SELECT_ACTIVE_ADMIN_BY_EMAIL = (
    "SELECT id FROM employees "
    "WHERE email = %s AND role = 'admin' AND is_active FOR SHARE;"
)
ASSIGN_COMPANY_ADMIN = (
    "INSERT INTO company_admins (admin_id, company_id, assigned_by) "
    "VALUES (%s, %s, %s) ON CONFLICT (admin_id, company_id) "
    "DO UPDATE SET is_active = TRUE, assigned_by = EXCLUDED.assigned_by;"
)
RELEASE_COMPANY_ADMIN = (
    "UPDATE company_admins SET is_active = FALSE "
    "WHERE admin_id = %s AND company_id = %s AND is_active "
    "RETURNING admin_id;"
)
INSERT_AUDIT = (
    "INSERT INTO platform_audit_log "
    "(actor_id, action, target_type, target_id, details) "
    "VALUES (%s, %s, %s, %s, %s);"
)


class NotFoundError(Exception):
    pass


class OrphanedCompanyError(Exception):
    def __init__(self, companies: list):
        super().__init__("Empresas sin dueno activo")
        self.companies = companies


class CompanyRepository:
    def list_owners(self) -> list:
        return self._fetch_all(SELECT_OWNERS)

    def get_owner(self, owner_id: int) -> Optional[dict]:
        return self._fetch_one(SELECT_OWNER, (owner_id,))

    def create_owner(self, owner_data: dict, actor_id: int) -> int:
        with db_cursor() as cursor:
            cursor.execute(INSERT_OWNER, (
                owner_data["name"],
                owner_data["email"],
                owner_data["password_hash"],
            ))
            owner_id = int(dict(cursor.fetchone())["id"])
            self._audit(cursor, actor_id, "owner.create", "owner", owner_id, {
                "email": owner_data["email"],
            })
            return owner_id

    def update_owner(
        self, owner_id: int, owner_data: dict, actor_id: int
    ) -> None:
        with db_cursor() as cursor:
            cursor.execute(UPDATE_OWNER, (
                owner_data["name"], owner_data["email"], owner_id
            ))
            if cursor.fetchone() is None:
                raise NotFoundError()
            self._audit(cursor, actor_id, "owner.update", "owner", owner_id, {
                "name": owner_data["name"],
                "email": owner_data["email"],
            })

    def set_owner_active(
        self, owner_id: int, is_active: bool, actor_id: int
    ) -> None:
        with db_cursor() as cursor:
            if not is_active:
                self._ensure_no_orphans(cursor, owner_id)
            cursor.execute(UPDATE_OWNER_ACTIVE, (is_active, owner_id))
            if cursor.fetchone() is None:
                raise NotFoundError()
            action = "owner.activate" if is_active else "owner.deactivate"
            self._audit(cursor, actor_id, action, "owner", owner_id, {})

    def reset_owner_password(
        self, owner_id: int, password_hash: str, actor_id: int
    ) -> dict:
        with db_cursor() as cursor:
            cursor.execute(RESET_OWNER_PASSWORD, (password_hash, owner_id))
            row = cursor.fetchone()
            if row is None:
                raise NotFoundError()
            self._audit(
                cursor, actor_id, "owner.reset_password", "owner", owner_id, {}
            )
            return dict(row)

    def admin_company_ids(self, admin_id: int) -> list:
        return [
            row["company_id"]
            for row in self._fetch_all(SELECT_ADMIN_COMPANY_IDS, (admin_id,))
        ]

    def admin_has_company(self, admin_id: int, company_id: int) -> bool:
        return self._fetch_one(
            SELECT_ADMIN_COMPANY, (admin_id, company_id)
        ) is not None

    def owner_has_company(self, owner_id: int, company_id: int) -> bool:
        return self._fetch_one(
            SELECT_OWNER_COMPANY, (owner_id, company_id)
        ) is not None

    def list_owner_companies(self, owner_id: int) -> list:
        return self._fetch_all(SELECT_OWNER_COMPANIES, (owner_id,))

    def get_owner_company(
        self, owner_id: int, company_id: int
    ) -> Optional[dict]:
        return self._fetch_one(
            SELECT_OWNER_COMPANY_DETAIL, (owner_id, company_id)
        )

    def set_company_active(
        self, company_id: int, is_active: bool, actor_id: int
    ) -> None:
        with db_cursor() as cursor:
            cursor.execute(UPDATE_COMPANY_ACTIVE, (is_active, company_id))
            if cursor.fetchone() is None:
                raise NotFoundError()
            action = "company.activate" if is_active else "company.deactivate"
            self._audit(cursor, actor_id, action, "company", company_id, {})

    def invite_admin(
        self, company_id: int, admin_data: dict, actor_id: int
    ) -> int:
        with db_cursor() as cursor:
            cursor.execute(INSERT_ADMIN, (
                admin_data["name"],
                admin_data["email"],
                admin_data["password_hash"],
            ))
            admin_id = int(dict(cursor.fetchone())["id"])
            cursor.execute(
                ASSIGN_COMPANY_ADMIN, (admin_id, company_id, actor_id)
            )
            self._audit(
                cursor, actor_id, "company.invite_admin", "company",
                company_id, {"admin_id": admin_id,
                             "email": admin_data["email"]},
            )
            return admin_id

    def assign_admin_by_email(
        self, company_id: int, email: str, actor_id: int
    ) -> int:
        with db_cursor() as cursor:
            cursor.execute(SELECT_ACTIVE_ADMIN_BY_EMAIL, (email,))
            row = cursor.fetchone()
            if row is None:
                raise NotFoundError()
            admin_id = int(dict(row)["id"])
            cursor.execute(
                ASSIGN_COMPANY_ADMIN, (admin_id, company_id, actor_id)
            )
            self._audit(
                cursor, actor_id, "company.assign_admin", "company",
                company_id, {"admin_id": admin_id},
            )
            return admin_id

    def unassign_admin(
        self, company_id: int, admin_id: int, actor_id: int
    ) -> None:
        with db_cursor() as cursor:
            cursor.execute(RELEASE_COMPANY_ADMIN, (admin_id, company_id))
            if cursor.fetchone() is None:
                raise NotFoundError()
            self._audit(
                cursor, actor_id, "company.unassign_admin", "company",
                company_id, {"admin_id": admin_id},
            )

    def list_companies(self) -> list:
        return self._fetch_all(SELECT_COMPANIES)

    def get_company(self, company_id: int) -> Optional[dict]:
        return self._fetch_one(SELECT_COMPANY, (company_id,))

    def create_company(
        self, company_data: dict, owner_id: int, actor_id: int
    ) -> int:
        with db_cursor() as cursor:
            cursor.execute(LOCK_ACTIVE_OWNER, (owner_id,))
            if cursor.fetchone() is None:
                raise NotFoundError()
            cursor.execute(INSERT_COMPANY, self._company_params(company_data))
            company_id = int(dict(cursor.fetchone())["id"])
            cursor.execute(INSERT_COMPANY_OWNER, (owner_id, company_id))
            self._audit(
                cursor, actor_id, "company.create", "company", company_id,
                dict(company_data, owner_id=owner_id),
            )
            return company_id

    def update_company(
        self, company_id: int, company_data: dict, actor_id: int
    ) -> None:
        with db_cursor() as cursor:
            cursor.execute(
                UPDATE_COMPANY,
                self._company_params(company_data) + (company_id,),
            )
            if cursor.fetchone() is None:
                raise NotFoundError()
            self._audit(
                cursor, actor_id, "company.update", "company", company_id,
                company_data,
            )

    def assign_owner(
        self, company_id: int, owner_id: int, actor_id: int
    ) -> None:
        with db_cursor() as cursor:
            cursor.execute(LOCK_COMPANY, (company_id,))
            if cursor.fetchone() is None:
                raise NotFoundError()
            cursor.execute(LOCK_ACTIVE_OWNER, (owner_id,))
            if cursor.fetchone() is None:
                raise NotFoundError()
            cursor.execute(INSERT_COMPANY_OWNER, (owner_id, company_id))
            if cursor.fetchone() is not None:
                self._audit(
                    cursor, actor_id, "company.assign_owner", "company",
                    company_id, {"owner_id": owner_id},
                )

    def unassign_owner(
        self, company_id: int, owner_id: int, actor_id: int
    ) -> None:
        with db_cursor() as cursor:
            cursor.execute(LOCK_COMPANY, (company_id,))
            if cursor.fetchone() is None:
                raise NotFoundError()
            self._ensure_no_orphans(cursor, owner_id, company_id)
            cursor.execute(DELETE_COMPANY_OWNER, (owner_id, company_id))
            if cursor.fetchone() is None:
                raise NotFoundError()
            self._audit(
                cursor, actor_id, "company.unassign_owner", "company",
                company_id, {"owner_id": owner_id},
            )

    def _ensure_no_orphans(
        self, cursor, owner_id: int, company_id: Optional[int] = None
    ) -> None:
        cursor.execute(
            SELECT_COMPANIES_LEFT_WITHOUT_OWNER,
            (owner_id, company_id, company_id, owner_id),
        )
        orphans = [dict(row) for row in cursor.fetchall()]
        if orphans:
            raise OrphanedCompanyError(orphans)

    def _company_params(self, company_data: dict) -> tuple:
        return (
            company_data["legal_name"],
            company_data.get("trade_name"),
            company_data.get("rfc"),
            company_data.get("registro_patronal"),
            company_data.get("entidad_federativa"),
        )

    def _audit(
        self, cursor, actor_id: int, action: str, target_type: str,
        target_id: int, details: dict,
    ) -> None:
        cursor.execute(INSERT_AUDIT, (
            actor_id, action, target_type, target_id, Json(details)
        ))

    def _fetch_one(self, query: str, params: tuple) -> Optional[dict]:
        with db_cursor() as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None

    def _fetch_all(self, query: str, params: tuple = ()) -> list:
        with db_cursor() as cursor:
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]


company_repository = CompanyRepository()
