/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
export async function up(knex) {
    // 1. Add a new column with the correct type
    await knex.schema.alterTable('soccer_2025_fixtures', (table) => {
      table.timestamp('date_time_new', { useTz: true });
    });
  
    // 2. Copy and convert existing values (assumes all are in UTC or have +00 at the end)
    await knex.raw(`
      UPDATE soccer_2025_fixtures
      SET date_time_new = 
        CASE
          WHEN date_time IS NULL THEN NULL
          ELSE date_time::timestamptz
        END
    `);
  
    // 3. Drop the old column
    await knex.schema.alterTable('soccer_2025_fixtures', (table) => {
      table.dropColumn('date_time');
    });
  
    // 4. Rename the new column to the original name
    await knex.schema.alterTable('soccer_2025_fixtures', (table) => {
      table.renameColumn('date_time_new', 'date_time');
    });
  }
  
  /**
   * @param { import("knex").Knex } knex
   * @returns { Promise<void> }
   */
  export async function down(knex) {
    // 1. Add the old column back as string
    await knex.schema.alterTable('soccer_2025_fixtures', (table) => {
      table.string('date_time_old');
    });
  
    // 2. Copy values back as ISO string
    await knex.raw(`
      UPDATE soccer_2025_fixtures
      SET date_time_old = to_char(date_time AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"')
    `);
  
    // 3. Drop the new column
    await knex.schema.alterTable('soccer_2025_fixtures', (table) => {
      table.dropColumn('date_time');
    });
  
    // 4. Rename the old column back
    await knex.schema.alterTable('soccer_2025_fixtures', (table) => {
      table.renameColumn('date_time_old', 'date_time');
    });
  }