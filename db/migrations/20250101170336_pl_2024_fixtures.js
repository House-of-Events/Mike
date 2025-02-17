/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
exports.up = function (knex) {
  return knex.schema.createTable('soccer_2024_pl_fixtures', (table) => {
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
    table.date('date');
    table.string('time');
    table.dateTime('date_time');
    table.dateTime('date_created').defaultTo(knex.fn.now());
    table.string('league').defaultTo('Premier League');
    table.boolean('informed').defaultTo(false);
    table.string('notification_sent_at');
  });
};

/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
exports.down = function (knex) {
  return knex.schema.dropTable('soccer_2024_pl_fixtures');
};
