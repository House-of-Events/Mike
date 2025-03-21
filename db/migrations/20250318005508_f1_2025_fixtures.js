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
        table.dateTime('date_time');
        table.dateTime('date_created').defaultTo(knex.fn.now());
        table.boolean('informed').defaultTo(false);
        table.string('notification_sent_at');
    });
  
};

/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
export async function down(knex) {
    return knex.schema.dropTable('f1_2025_fixtures');
};
