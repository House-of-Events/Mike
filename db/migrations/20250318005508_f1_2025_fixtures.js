/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
export async function up(knex) {
    return knex.schema.createTable('f1_2025_fixtures', (table) => {
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
        table.integer('round');
        table.string('circuit');
        table.string('city');
        table.string('race_type');
        table.string('date');
        table.string('time');
        table.string('date_time');
        table.string('status').checkIn(['pending', 'completed', 'delayed', 'cancelled']);
        table.string('notification_sent_at');
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
    return knex.schema.dropTable('f1_2025_fixtures');
};
