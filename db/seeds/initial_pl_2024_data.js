/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
exports.seed = async function (knex) {
  // Deletes ALL existing entries
  await knex('soccer_2024_pl_fixtures').del();

  // Inserts seed entries
  await knex('soccer_2024_pl_fixtures').insert([
    {
      id: 'mat_123456',
      fixture_id: 'FX123',
      match_id: 'M123',
      home_team: 'Manchester United',
      away_team: 'Chelsea',
      venue: 'Old Trafford',
      date: '2024-08-10',
      time: '15:00',
      date_time: '2024-08-10 15:00:00',
      date_created: knex.fn.now(),
      league: 'Premier League',
      informed: false,
      notification_sent_at: null,
    },
    {
      id: 'mat_234567',
      fixture_id: 'FX124',
      match_id: 'M124',
      home_team: 'Liverpool',
      away_team: 'Arsenal',
      venue: 'Anfield',
      date: '2024-08-11',
      time: '17:30',
      date_time: '2024-08-11 17:30:00',
      date_created: knex.fn.now(),
      league: 'Premier League',
      informed: false,
      notification_sent_at: null,
    },
    {
      id: 'mat_345678',
      fixture_id: 'FX125',
      match_id: 'M125',
      home_team: 'Manchester City',
      away_team: 'Tottenham',
      venue: 'Etihad Stadium',
      date: '2024-08-12',
      time: '20:00',
      date_time: '2024-08-12 20:00:00',
      date_created: knex.fn.now(),
      league: 'Premier League',
      informed: true,
      notification_sent_at: '2024-08-10 10:00:00',
    },
  ]);
};
