-- =============================================================================
-- PROJECT: supa-meta-budget
-- DESCRIPTION: Recreated Schema based on Database Inspection
-- VERSION: 1.2 (Added dim_users & Fixed Relationships)
-- =============================================================================
BEGIN;

CREATE TYPE transaction_type_enum AS ENUM ('INCOME', 'EXPENSE', 'TRANSFER');
CREATE TYPE transaction_status_enum AS ENUM ('COMPLETED', 'PENDING');
CREATE TYPE transaction_sentiment_enum AS ENUM ('Fundament', 'Rozwój', 'Nagroda', 'Niedosyt', 'Mega', 'Rutyna', 'Tragedia');

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TABLE dim_wallets (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_name varchar NOT NULL,
    wallet_name varchar NOT NULL,
    is_active boolean DEFAULT true,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    deleted_at timestamptz
);

CREATE TABLE dim_users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    alias varchar NOT NULL,
    color_hex varchar DEFAULT '#888888',
    default_wallet_fk uuid REFERENCES dim_wallets(id) ON DELETE SET NULL, 
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

CREATE TABLE dim_categories (
    subcategory_id serial PRIMARY KEY,
    category_id int NOT NULL,
    category varchar NOT NULL,
    subcategory varchar NOT NULL,
    type transaction_type_enum,
    color_hex varchar,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    deleted_at timestamptz,
    UNIQUE(category, subcategory)
);


CREATE TABLE dim_budget_goals (
    id serial PRIMARY KEY,
    tag varchar NOT NULL, 
    monthly_target_amount numeric NOT NULL CHECK (monthly_target_amount >= 0),
    is_active boolean DEFAULT true,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    deleted_at timestamptz,
    UNIQUE(tag) 
);


CREATE TABLE fact_transactions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    amount numeric NOT NULL,
    transaction_date date NOT NULL DEFAULT now(),

    wallet_fk uuid NOT NULL REFERENCES dim_wallets(id),
    to_wallet_fk uuid REFERENCES dim_wallets(id),
    subcategory_fk int NOT NULL REFERENCES dim_categories(subcategory_id),
    created_by_fk uuid NOT NULL REFERENCES dim_users(id),
    
    status transaction_status_enum DEFAULT 'COMPLETED',
    sentiment transaction_sentiment_enum,
    tag varchar,
    is_excluded_from_stats boolean DEFAULT false,
    attachment_path varchar,
    attachment_type varchar,
    description text,
    
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    deleted_at timestamptz
);


CREATE TRIGGER trg_wallets_updated_at BEFORE UPDATE ON dim_wallets FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON dim_users FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER trg_categories_updated_at BEFORE UPDATE ON dim_categories FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER trg_budget_goals_updated_at BEFORE UPDATE ON dim_budget_goals FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER trg_transactions_updated_at BEFORE UPDATE ON fact_transactions FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();


CREATE INDEX idx_fact_transactions_date ON fact_transactions(transaction_date);
CREATE INDEX idx_fact_transactions_wallet ON fact_transactions(wallet_fk);
CREATE INDEX idx_fact_transactions_subcategory ON fact_transactions(subcategory_fk);
CREATE INDEX idx_fact_transactions_user ON fact_transactions(created_by_fk);

COMMIT;