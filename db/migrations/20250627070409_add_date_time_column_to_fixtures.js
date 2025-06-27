/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
export async function up(knex) {
    return knex.schema.alterTable('fixtures', (table) => {
      table.timestamp('date_time').nullable();
    });
  };
  
  
  /**
   * @param { import("knex").Knex } knex
   * @returns { Promise<void> }
   */
  export async function down(knex) {
    return knex.schema.alterTable('fixtures', (table) => {
      table.dropColumn('date_time');
    });
  }; 