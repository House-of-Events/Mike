/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
exports.up = function(knex) {
    return knex.schema.table('soccer_2024_pl_fixtures', (table) => {
        table.time('time');
    });
  
};

/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
exports.down = function(knex) {
    return knex.schema.table('soccer_2024_pl_fixtures', (table) => {
        table.dropColumn('time');
    });
  
};
