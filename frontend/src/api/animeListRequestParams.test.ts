import { expect, it } from 'vitest';
import { animeListRequestParams } from './anime';
it('uses the same cache identity for defaults and empty UI filters', () => {
  expect(animeListRequestParams({ page:1, page_size:50, ordering:'-score', group_franchises:true })).toEqual(
    animeListRequestParams({ page:1, page_size:50, ordering:'-score', group_franchises:true,
      search:'', genres:[], genre_logic:'OR', type:[], kind:[], show_only_franchises:false, excluded_library_statuses:[] }));
});
it('keeps meaningful filter changes in the wire identity', () => {
  const result=animeListRequestParams({ genres:['Драма','Комедия'], status:['ongoing','released'], score_from:0 });
  expect(result.genres).toBe('Драма,Комедия'); expect(result.genre_logic).toBe('OR');
  expect(result.status).toBe('ongoing,released'); expect(result.score_from).toBe(0);
});
it('preserves the unfiltered API default contract', () => { expect(animeListRequestParams()).toEqual({}); });
