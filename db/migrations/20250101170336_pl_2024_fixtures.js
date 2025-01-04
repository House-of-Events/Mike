/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
exports.up = function(knex) {
    return knex.schema.createTable('soccer_2024_pl_fixtures', (table) => {
        table.increments('id').primary().unique();
        table.string('home_team');
        table.string('away_team');
        table.string('city');
        table.string('stadium');
        table.dateTime('date');
        table.string('league').defaultTo('Premier League');
    });
};

/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
exports.down = function(knex) {
    return knex.schema.dropTable('soccer_2024_pl_fixtures');
};
