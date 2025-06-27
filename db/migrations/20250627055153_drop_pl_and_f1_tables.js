/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
export async function up(knex) {
    // Drop the old sport-specific fixture tables
    await knex.schema.dropTableIfExists('f1_2025_fixtures');
    await knex.schema.dropTableIfExists('soccer_2025_fixtures');
  };
  
  /**
   * @param { import("knex").Knex } knex
   * @returns { Promise<void> }
   */
  export async function down(knex) {
    // Note: This down migration doesn't recreate the old tables
    // as we're moving to the unified fixtures table structure
    // If you need to rollback, you would need to recreate the old tables manually
    console.log('Warning: Down migration does not recreate old tables. Manual recreation required if needed.');
  }; 