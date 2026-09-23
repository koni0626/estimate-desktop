-- SQLite 3 schema contract for a fresh estimate2 installation.
-- Generated from the Alembic-migrated empty database; contains no user data.
-- Implementations should express this through SQLAlchemy models and Alembic migrations.

CREATE TABLE approval_requests (
	id INTEGER NOT NULL,
	company_id INTEGER NOT NULL,
	revision_id INTEGER NOT NULL,
	requester_id INTEGER NOT NULL,
	route_version INTEGER NOT NULL,
	snapshot JSON NOT NULL,
	status VARCHAR(25) NOT NULL,
	created_at DATETIME NOT NULL,
	CONSTRAINT pk_approval_requests PRIMARY KEY (id),
	CONSTRAINT fk_approval_requests_company_id_requester_id_memberships FOREIGN KEY(company_id, requester_id) REFERENCES memberships (company_id, id),
	CONSTRAINT fk_approval_requests_company_id_revision_id_revisions FOREIGN KEY(company_id, revision_id) REFERENCES revisions (company_id, id),
	CONSTRAINT fk_approval_requests_company_id_companies FOREIGN KEY(company_id) REFERENCES companies (id),
	CONSTRAINT uq_approval_requests_company_id_id UNIQUE (company_id, id)
);

CREATE TABLE approval_steps (
	id INTEGER NOT NULL,
	company_id INTEGER NOT NULL,
	request_id INTEGER NOT NULL,
	position INTEGER NOT NULL,
	name VARCHAR(100) NOT NULL,
	approver_id INTEGER NOT NULL,
	status VARCHAR(25) NOT NULL,
	comment TEXT NOT NULL,
	decided_at DATETIME,
	CONSTRAINT pk_approval_steps PRIMARY KEY (id),
	CONSTRAINT fk_approval_steps_company_id_approver_id_memberships FOREIGN KEY(company_id, approver_id) REFERENCES memberships (company_id, id),
	CONSTRAINT fk_approval_steps_company_id_request_id_approval_requests FOREIGN KEY(company_id, request_id) REFERENCES approval_requests (company_id, id),
	CONSTRAINT fk_approval_steps_company_id_companies FOREIGN KEY(company_id) REFERENCES companies (id),
	CONSTRAINT uq_approval_steps_company_id_request_id_position UNIQUE (company_id, request_id, position)
);

CREATE TABLE audit_logs (
	id INTEGER NOT NULL,
	company_id INTEGER NOT NULL,
	quote_id INTEGER,
	actor_id INTEGER NOT NULL,
	action VARCHAR(80) NOT NULL,
	detail TEXT NOT NULL,
	created_at DATETIME NOT NULL,
	CONSTRAINT pk_audit_logs PRIMARY KEY (id),
	CONSTRAINT fk_audit_logs_company_id_actor_id_memberships FOREIGN KEY(company_id, actor_id) REFERENCES memberships (company_id, id),
	CONSTRAINT fk_audit_logs_company_id_quote_id_quotes FOREIGN KEY(company_id, quote_id) REFERENCES quotes (company_id, id),
	CONSTRAINT fk_audit_logs_company_id_companies FOREIGN KEY(company_id) REFERENCES companies (id)
);

CREATE TABLE companies (
	id INTEGER NOT NULL,
	name VARCHAR(120) NOT NULL,
	address VARCHAR(300) NOT NULL,
	phone VARCHAR(60) NOT NULL,
	active BOOLEAN NOT NULL,
	approval_mode VARCHAR(20) NOT NULL,
	route JSON NOT NULL,
	route_version INTEGER NOT NULL,
	next_number INTEGER NOT NULL,
	next_invoice INTEGER DEFAULT '1' NOT NULL,
	seal_default BOOLEAN DEFAULT 'false' NOT NULL,
	registration_number VARCHAR(14) DEFAULT '' NOT NULL,
	bank_details VARCHAR(500) DEFAULT '' NOT NULL,
	CONSTRAINT pk_companies PRIMARY KEY (id)
);

CREATE TABLE customers (
	id INTEGER NOT NULL,
	company_id INTEGER NOT NULL,
	name VARCHAR(150) NOT NULL,
	contact VARCHAR(120) NOT NULL,
	address VARCHAR(300) NOT NULL,
	email VARCHAR(200) NOT NULL,
	CONSTRAINT pk_customers PRIMARY KEY (id),
	CONSTRAINT fk_customers_company_id_companies FOREIGN KEY(company_id) REFERENCES companies (id),
	CONSTRAINT uq_customers_company_id_id UNIQUE (company_id, id)
);

CREATE TABLE departments (
	id INTEGER NOT NULL,
	company_id INTEGER NOT NULL,
	name VARCHAR(100) NOT NULL,
	CONSTRAINT pk_departments PRIMARY KEY (id),
	CONSTRAINT fk_departments_company_id_companies FOREIGN KEY(company_id) REFERENCES companies (id),
	CONSTRAINT uq_departments_company_id_id UNIQUE (company_id, id),
	CONSTRAINT uq_departments_company_id_name UNIQUE (company_id, name)
);

CREATE TABLE invoices (
	id INTEGER NOT NULL,
	company_id INTEGER NOT NULL,
	order_id INTEGER NOT NULL,
	number VARCHAR(40),
	status VARCHAR(20) NOT NULL,
	payload JSON NOT NULL,
	total NUMERIC(16, 0) NOT NULL,
	issue_on DATE NOT NULL,
	transaction_on DATE NOT NULL,
	due_on DATE NOT NULL,
	paid_on DATE,
	payment_note TEXT NOT NULL,
	pdf BLOB,
	lock_version INTEGER NOT NULL,
	updated_at DATETIME NOT NULL,
	CONSTRAINT pk_invoices PRIMARY KEY (id),
	CONSTRAINT fk_invoices_company_id_order_id_orders FOREIGN KEY(company_id, order_id) REFERENCES orders (company_id, id),
	CONSTRAINT fk_invoices_company_id_companies FOREIGN KEY(company_id) REFERENCES companies (id),
	CONSTRAINT uq_invoices_company_id_id UNIQUE (company_id, id),
	CONSTRAINT uq_invoices_company_id_number UNIQUE (company_id, number)
);

CREATE TABLE login_sessions (
	id VARCHAR(64) NOT NULL,
	membership_id INTEGER NOT NULL,
	expires_at DATETIME NOT NULL,
	CONSTRAINT pk_login_sessions PRIMARY KEY (id),
	CONSTRAINT fk_login_sessions_membership_id_memberships FOREIGN KEY(membership_id) REFERENCES memberships (id)
);

CREATE TABLE memberships (
	id INTEGER NOT NULL,
	company_id INTEGER NOT NULL,
	user_id INTEGER NOT NULL,
	role VARCHAR(30) NOT NULL,
	department_id INTEGER,
	section_id INTEGER,
	active BOOLEAN NOT NULL,
	CONSTRAINT pk_memberships PRIMARY KEY (id),
	CONSTRAINT fk_memberships_company_id_department_id_section_id_sections FOREIGN KEY(company_id, department_id, section_id) REFERENCES sections (company_id, department_id, id),
	CONSTRAINT fk_memberships_company_id_department_id_departments FOREIGN KEY(company_id, department_id) REFERENCES departments (company_id, id),
	CONSTRAINT fk_memberships_company_id_companies FOREIGN KEY(company_id) REFERENCES companies (id),
	CONSTRAINT fk_memberships_user_id_users FOREIGN KEY(user_id) REFERENCES users (id),
	CONSTRAINT uq_memberships_company_id_id UNIQUE (company_id, id),
	CONSTRAINT uq_memberships_company_id_user_id UNIQUE (company_id, user_id)
);

CREATE TABLE orders (
	id INTEGER NOT NULL,
	company_id INTEGER NOT NULL,
	quote_id INTEGER NOT NULL,
	revision_id INTEGER NOT NULL,
	ordered_on DATE NOT NULL,
	delivery_on DATE,
	status VARCHAR(20) NOT NULL,
	note TEXT NOT NULL,
	lock_version INTEGER NOT NULL,
	updated_at DATETIME NOT NULL,
	CONSTRAINT pk_orders PRIMARY KEY (id),
	CONSTRAINT fk_orders_company_id_quote_id_revision_id_revisions FOREIGN KEY(company_id, quote_id, revision_id) REFERENCES revisions (company_id, quote_id, id),
	CONSTRAINT fk_orders_company_id_quote_id_quotes FOREIGN KEY(company_id, quote_id) REFERENCES quotes (company_id, id),
	CONSTRAINT fk_orders_company_id_companies FOREIGN KEY(company_id) REFERENCES companies (id),
	CONSTRAINT uq_orders_company_id_id UNIQUE (company_id, id),
	CONSTRAINT uq_orders_company_id_quote_id UNIQUE (company_id, quote_id)
);

CREATE TABLE project_attachments (
	id INTEGER NOT NULL,
	company_id INTEGER NOT NULL,
	project_id INTEGER NOT NULL,
	upload_id VARCHAR(36) NOT NULL,
	filename VARCHAR(200) NOT NULL,
	size_bytes INTEGER NOT NULL,
	sha256 VARCHAR(64) NOT NULL,
	content BLOB NOT NULL,
	uploaded_by_id INTEGER NOT NULL,
	created_at DATETIME NOT NULL,
	CONSTRAINT pk_project_attachments PRIMARY KEY (id),
	CONSTRAINT ck_project_attachments_positive_size CHECK (size_bytes > 0),
	CONSTRAINT fk_project_attachments_company_id_project_id_projects FOREIGN KEY(company_id, project_id) REFERENCES projects (company_id, id),
	CONSTRAINT fk_project_attachments_company_id_uploaded_by_id_memberships FOREIGN KEY(company_id, uploaded_by_id) REFERENCES memberships (company_id, id),
	CONSTRAINT fk_project_attachments_company_id_companies FOREIGN KEY(company_id) REFERENCES companies (id),
	CONSTRAINT uq_project_attachments_company_id_project_id_upload_id UNIQUE (company_id, project_id, upload_id)
);

CREATE TABLE projects (
	id INTEGER NOT NULL,
	company_id INTEGER NOT NULL,
	customer_id INTEGER NOT NULL,
	owner_id INTEGER NOT NULL,
	department_id INTEGER,
	section_id INTEGER,
	title VARCHAR(150) NOT NULL,
	purpose TEXT NOT NULL,
	customer_contact VARCHAR(120) NOT NULL,
	customer_corporate_number VARCHAR(13) NOT NULL,
	status VARCHAR(25) NOT NULL,
	due_on DATE,
	external_url VARCHAR(1000) NOT NULL,
	lock_version INTEGER NOT NULL,
	updated_at DATETIME NOT NULL,
	CONSTRAINT pk_projects PRIMARY KEY (id),
	CONSTRAINT fk_projects_company_id_customer_id_customers FOREIGN KEY(company_id, customer_id) REFERENCES customers (company_id, id),
	CONSTRAINT fk_projects_company_id_department_id_section_id_sections FOREIGN KEY(company_id, department_id, section_id) REFERENCES sections (company_id, department_id, id),
	CONSTRAINT fk_projects_company_id_department_id_departments FOREIGN KEY(company_id, department_id) REFERENCES departments (company_id, id),
	CONSTRAINT fk_projects_company_id_owner_id_memberships FOREIGN KEY(company_id, owner_id) REFERENCES memberships (company_id, id),
	CONSTRAINT fk_projects_company_id_companies FOREIGN KEY(company_id) REFERENCES companies (id),
	CONSTRAINT uq_projects_company_id_id UNIQUE (company_id, id)
);

CREATE TABLE quotes (
	id INTEGER NOT NULL,
	project_id INTEGER,
	company_id INTEGER NOT NULL,
	number VARCHAR(40),
	creator_id INTEGER NOT NULL,
	owner_id INTEGER NOT NULL,
	department_id INTEGER,
	section_id INTEGER,
	created_at DATETIME NOT NULL,
	sales_status VARCHAR(20) DEFAULT 'open' NOT NULL,
	sales_version INTEGER DEFAULT '1' NOT NULL,
	sent_on DATE,
	CONSTRAINT pk_quotes PRIMARY KEY (id),
	CONSTRAINT fk_quotes_company_id_creator_id_memberships FOREIGN KEY(company_id, creator_id) REFERENCES memberships (company_id, id),
	CONSTRAINT fk_quotes_company_id_department_id_section_id_sections FOREIGN KEY(company_id, department_id, section_id) REFERENCES sections (company_id, department_id, id),
	CONSTRAINT fk_quotes_company_id_department_id_departments FOREIGN KEY(company_id, department_id) REFERENCES departments (company_id, id),
	CONSTRAINT fk_quotes_company_id_owner_id_memberships FOREIGN KEY(company_id, owner_id) REFERENCES memberships (company_id, id),
	CONSTRAINT fk_quotes_company_id_project_id_projects FOREIGN KEY(company_id, project_id) REFERENCES projects (company_id, id),
	CONSTRAINT fk_quotes_company_id_companies FOREIGN KEY(company_id) REFERENCES companies (id),
	CONSTRAINT uq_quotes_company_id_id UNIQUE (company_id, id),
	CONSTRAINT uq_quotes_company_id_number UNIQUE (company_id, number)
);

CREATE TABLE requirement_history (
	id INTEGER NOT NULL,
	company_id INTEGER NOT NULL,
	requirement_id INTEGER NOT NULL,
	version INTEGER NOT NULL,
	actor_id INTEGER NOT NULL,
	payload JSON NOT NULL,
	note VARCHAR(1000) NOT NULL,
	created_at DATETIME NOT NULL,
	CONSTRAINT pk_requirement_history PRIMARY KEY (id),
	CONSTRAINT fk_requirement_history_company_id_actor_id_memberships FOREIGN KEY(company_id, actor_id) REFERENCES memberships (company_id, id),
	CONSTRAINT fk_requirement_history_company_id_requirement_id_requirements FOREIGN KEY(company_id, requirement_id) REFERENCES requirements (company_id, id),
	CONSTRAINT fk_requirement_history_company_id_companies FOREIGN KEY(company_id) REFERENCES companies (id),
	CONSTRAINT uq_requirement_history_company_id_requirement_id_version UNIQUE (company_id, requirement_id, version)
);

CREATE TABLE requirements (
	id INTEGER NOT NULL,
	company_id INTEGER NOT NULL,
	project_id INTEGER NOT NULL,
	title VARCHAR(150) NOT NULL,
	description TEXT NOT NULL,
	acceptance TEXT NOT NULL,
	questions TEXT NOT NULL,
	priority VARCHAR(20) NOT NULL,
	scope VARCHAR(20) NOT NULL,
	status VARCHAR(20) NOT NULL,
	agreement JSON,
	lock_version INTEGER NOT NULL,
	updated_at DATETIME NOT NULL,
	CONSTRAINT pk_requirements PRIMARY KEY (id),
	CONSTRAINT fk_requirements_company_id_project_id_projects FOREIGN KEY(company_id, project_id) REFERENCES projects (company_id, id),
	CONSTRAINT fk_requirements_company_id_companies FOREIGN KEY(company_id) REFERENCES companies (id),
	CONSTRAINT uq_requirements_company_id_id UNIQUE (company_id, id)
);

CREATE TABLE revisions (
	id INTEGER NOT NULL,
	company_id INTEGER NOT NULL,
	quote_id INTEGER NOT NULL,
	version INTEGER NOT NULL,
	lock_version INTEGER NOT NULL,
	status VARCHAR(25) NOT NULL,
	payload JSON NOT NULL,
	subtotal NUMERIC(16, 0) NOT NULL,
	tax NUMERIC(16, 0) NOT NULL,
	total NUMERIC(16, 0) NOT NULL,
	pdf BLOB,
	issued_at DATETIME,
	updated_at DATETIME NOT NULL,
	CONSTRAINT pk_revisions PRIMARY KEY (id),
	CONSTRAINT fk_revisions_company_id_quote_id_quotes FOREIGN KEY(company_id, quote_id) REFERENCES quotes (company_id, id),
	CONSTRAINT fk_revisions_company_id_companies FOREIGN KEY(company_id) REFERENCES companies (id),
	CONSTRAINT uq_revisions_company_id_id UNIQUE (company_id, id),
	CONSTRAINT uq_revisions_company_id_quote_id_id UNIQUE (company_id, quote_id, id),
	CONSTRAINT uq_revisions_company_id_quote_id_version UNIQUE (company_id, quote_id, version)
);

CREATE TABLE seals (
	id INTEGER NOT NULL,
	company_id INTEGER NOT NULL,
	image BLOB NOT NULL,
	active BOOLEAN NOT NULL,
	created_at DATETIME NOT NULL,
	CONSTRAINT pk_seals PRIMARY KEY (id),
	CONSTRAINT fk_seals_company_id_companies FOREIGN KEY(company_id) REFERENCES companies (id),
	CONSTRAINT uq_seals_company_id_id UNIQUE (company_id, id)
);

CREATE TABLE sections (
	id INTEGER NOT NULL,
	company_id INTEGER NOT NULL,
	department_id INTEGER NOT NULL,
	name VARCHAR(100) NOT NULL,
	CONSTRAINT pk_sections PRIMARY KEY (id),
	CONSTRAINT fk_sections_company_id_department_id_departments FOREIGN KEY(company_id, department_id) REFERENCES departments (company_id, id),
	CONSTRAINT fk_sections_company_id_companies FOREIGN KEY(company_id) REFERENCES companies (id),
	CONSTRAINT uq_sections_company_id_department_id_id UNIQUE (company_id, department_id, id),
	CONSTRAINT uq_sections_company_id_id UNIQUE (company_id, id)
);

CREATE TABLE users (
	id INTEGER NOT NULL,
	username VARCHAR(80) NOT NULL,
	display_name VARCHAR(100) NOT NULL,
	password_hash VARCHAR(300) NOT NULL,
	CONSTRAINT pk_users PRIMARY KEY (id),
	CONSTRAINT uq_users_username UNIQUE (username)
);

CREATE INDEX ix_approval_requests_revision_id ON approval_requests (revision_id);

CREATE INDEX ix_approval_steps_request_id ON approval_steps (request_id);

CREATE INDEX ix_project_attachments_company_id ON project_attachments (company_id);

CREATE INDEX ix_project_attachments_project_id ON project_attachments (project_id);

CREATE INDEX ix_projects_company_id ON projects (company_id);

CREATE INDEX ix_quotes_company_id ON quotes (company_id);

CREATE INDEX ix_quotes_project_id ON quotes (project_id);

CREATE INDEX ix_requirements_company_id ON requirements (company_id);

CREATE INDEX ix_requirements_project_id ON requirements (project_id);

CREATE INDEX ix_revisions_quote_id ON revisions (quote_id);

CREATE INDEX ix_seals_company_id ON seals (company_id);

CREATE UNIQUE INDEX uq_invoices_active_order ON invoices (company_id, order_id) WHERE status <> 'void';
