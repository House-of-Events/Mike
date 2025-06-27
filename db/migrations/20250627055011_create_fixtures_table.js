/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
export async function up(knex) {
    return knex.schema.createTable('fixtures', (table) => {
      table
        .string('id')
        .primary()
        .defaultTo(
          knex.raw(
            "concat('fix_', lpad(floor(random() * 1000000)::text, 6, '0'))"
          )
        );
      table.string('match_id').unique().notNullable();
      table.string('sport_type').notNullable();
      table.jsonb('fixture_data').notNullable();
      table.string('status').checkIn(['pending', 'completed', 'delayed', 'cancelled']);
      table.boolean('processed').defaultTo(false);
      table.timestamp('date_processed').nullable();
      
      // Timestamp fields
      table.timestamp('date_created').defaultTo(knex.fn.now());
      table.timestamp('date_updated').defaultTo(knex.fn.now());
      table.timestamp('date_deleted').nullable();
      
      // Indexes for better performance
      table.index(['sport_type']);
      table.index(['status']);
      table.index(['match_id']);
      table.index(['fixture_data'], 'gin'); 
    });
  };
  
  /**
   * @param { import("knex").Knex } knex
   * @returns { Promise<void> }
   */
  export async function down(knex) {
    return knex.schema.dropTable('fixtures');
  }; 