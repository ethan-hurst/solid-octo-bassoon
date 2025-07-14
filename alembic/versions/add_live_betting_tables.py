"""Add live betting tables

Revision ID: 002_live_betting
Revises: 001_initial
Create Date: 2025-01-14 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_live_betting'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade():
    # Live games table
    op.create_table(
        'live_games',
        sa.Column('game_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('sport', sa.String(50), nullable=False),
        sa.Column('home_team', sa.String(100), nullable=False),
        sa.Column('away_team', sa.String(100), nullable=False),
        sa.Column('game_state', postgresql.JSONB, nullable=False),
        sa.Column('current_score', postgresql.JSONB, nullable=False),
        sa.Column('game_clock', sa.String(20)),
        sa.Column('quarter_period', sa.Integer),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    # Live odds updates table
    op.create_table(
        'live_odds_updates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('game_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('live_games.game_id'), nullable=False),
        sa.Column('bookmaker', sa.String(50), nullable=False),
        sa.Column('bet_type', sa.String(50), nullable=False),
        sa.Column('odds_before', sa.Numeric(10, 3)),
        sa.Column('odds_after', sa.Numeric(10, 3)),
        sa.Column('line_before', sa.Numeric(10, 2)),
        sa.Column('line_after', sa.Numeric(10, 2)),
        sa.Column('significance_score', sa.Numeric(5, 4)),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    # Live events table
    op.create_table(
        'live_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('game_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('live_games.game_id'), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_description', sa.Text),
        sa.Column('event_data', postgresql.JSONB),
        sa.Column('game_clock', sa.String(20)),
        sa.Column('impact_score', sa.Numeric(5, 3)),
        sa.Column('probability_change', postgresql.JSONB),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    # Live predictions table
    op.create_table(
        'live_predictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('game_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('live_games.game_id'), nullable=False),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('home_win_probability', sa.Numeric(5, 4), nullable=False),
        sa.Column('away_win_probability', sa.Numeric(5, 4), nullable=False),
        sa.Column('draw_probability', sa.Numeric(5, 4)),
        sa.Column('confidence_score', sa.Numeric(5, 4), nullable=False),
        sa.Column('features_used', postgresql.JSONB),
        sa.Column('prediction_timestamp', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    # Live value bets table
    op.create_table(
        'live_value_bets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('game_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('live_games.game_id'), nullable=False),
        sa.Column('bookmaker', sa.String(50), nullable=False),
        sa.Column('bet_type', sa.String(50), nullable=False),
        sa.Column('selection', sa.String(100), nullable=False),
        sa.Column('odds', sa.Numeric(10, 3), nullable=False),
        sa.Column('fair_odds', sa.Numeric(10, 3), nullable=False),
        sa.Column('edge', sa.Numeric(8, 6), nullable=False),
        sa.Column('confidence', sa.Numeric(5, 4), nullable=False),
        sa.Column('kelly_fraction', sa.Numeric(8, 6)),
        sa.Column('recommended_stake', sa.Numeric(10, 2)),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True))
    )
    
    # Live user subscriptions table
    op.create_table(
        'live_subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('subscription_type', sa.String(50), nullable=False),  # 'game', 'sport', 'team'
        sa.Column('subscription_target', sa.String(100), nullable=False),  # game_id, sport, team_name
        sa.Column('min_edge_threshold', sa.Numeric(5, 4), default=0.02),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    # Create indexes for performance
    op.create_index('idx_live_games_active', 'live_games', ['is_active', 'last_updated'])
    op.create_index('idx_live_games_sport', 'live_games', ['sport', 'is_active'])
    
    op.create_index('idx_live_odds_game_timestamp', 'live_odds_updates', ['game_id', 'timestamp'])
    op.create_index('idx_live_odds_bookmaker_timestamp', 'live_odds_updates', ['bookmaker', 'timestamp'])
    
    op.create_index('idx_live_events_game_timestamp', 'live_events', ['game_id', 'timestamp'])
    op.create_index('idx_live_events_type', 'live_events', ['event_type', 'timestamp'])
    
    op.create_index('idx_live_predictions_game_timestamp', 'live_predictions', ['game_id', 'prediction_timestamp'])
    op.create_index('idx_live_predictions_model', 'live_predictions', ['model_version', 'prediction_timestamp'])
    
    op.create_index('idx_live_value_bets_active', 'live_value_bets', ['is_active', 'detected_at'])
    op.create_index('idx_live_value_bets_game', 'live_value_bets', ['game_id', 'is_active'])
    op.create_index('idx_live_value_bets_edge', 'live_value_bets', ['edge'], postgresql_where=sa.text('is_active = true'))
    
    op.create_index('idx_live_subscriptions_user', 'live_subscriptions', ['user_id', 'is_active'])
    op.create_index('idx_live_subscriptions_type_target', 'live_subscriptions', ['subscription_type', 'subscription_target'])
    
    # Create TimescaleDB hypertables for time-series data
    op.execute("SELECT create_hypertable('live_odds_updates', 'timestamp');")
    op.execute("SELECT create_hypertable('live_events', 'timestamp');")
    op.execute("SELECT create_hypertable('live_predictions', 'prediction_timestamp');")
    op.execute("SELECT create_hypertable('live_value_bets', 'detected_at');")


def downgrade():
    # Drop TimescaleDB hypertables first
    op.execute("DROP TABLE IF EXISTS live_value_bets;")
    op.execute("DROP TABLE IF EXISTS live_predictions;")
    op.execute("DROP TABLE IF EXISTS live_events;")
    op.execute("DROP TABLE IF EXISTS live_odds_updates;")
    
    # Drop remaining tables
    op.drop_table('live_subscriptions')
    op.drop_table('live_games')