/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
export async function up(knex) {
  return knex.schema.createTable('soccer_2025_fixtures', (table) => {
    table
      .string('id')
      .primary()
      .defaultTo(
        knex.raw(
          "concat('mat_', lpad(floor(random() * 1000000)::text, 6, '0'))"
        )
      );
    table.string('fixture_id');
    table.string('match_id');
    table.string('home_team');
    table.string('away_team');
    table.string('venue');
    table.string('date');
    table.string('time');
    table.string('date_time');
    table.string('league');
    table.string('notification_sent_at');
    table.string('status').checkIn(['pending', 'completed', 'delayed', 'cancelled']);
    table.boolean('processed').defaultTo(false);
    table.timestamp('date_processed').nullable();
    
    // Timestamp fields
    table.timestamp('date_created').defaultTo(knex.fn.now());
    table.timestamp('date_updated').defaultTo(knex.fn.now());
    table.timestamp('date_deleted').nullable();
    
  });
};

/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
export async function down(knex) {
return knex.schema.dropTable('soccer_2024_pl_fixtures');
};
