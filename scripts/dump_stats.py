import configparser
import logging
from pprint import pprint
import sys

import pandas as pd
import pymysql

LOG = logging.getLogger(__name__)
COACH_QUERY = """
select vcn.coachid as naf_number, vcn.pn_uname as naf_name, vcn.oba_nation as nation, race_rank.race_name, race_rank.ranking as 'elo', 0 as 'race_rank', r.row_num as 'rank'
from view_coach_nation vcn
LEFT JOIN (
    SELECT ncv.coachID, ncv.raceID, race.name as race_name, ncv.ranking FROM naf_coachranking_variant ncv JOIN naf_race race on race.raceid = ncv.raceID WHERE variantid=13) as race_rank ON race_rank.coachID=vcn.coachid 
LEFT JOIN (
    SELECT 
    /*(@row_number:=@row_number + 1)*/ 1 AS row_num, coachID, maxrank 
    FROM(
         SELECT coachID, max(ranking) as maxrank
        FROM naf_coachranking_variant
        WHERE variantID=13
        GROUP BY coachID
        order by maxrank desc) as global) as r ON r.coachID=vcn.coachid
ORDER BY elo desc
"""


MATCH_QUERY = """
SELECT CONCAT(g.`date`,'T', LPAD(g.`hour`, 2, '0'),':00') as "date",
g.tournamentid as tournament_id, g.gameid as match_id,
t.tournamentname as tournament_name,
coach_home.pn_uname as home_coach,	race_h.name as home_race, CASE WHEN goalshome > goalsaway THEN 'W' WHEN goalsaway > goalshome THEN 'L' ELSE 'T' END as home_result, goalshome as home_score,
goalsaway as away_score, CASE WHEN goalshome < goalsaway THEN 'W' WHEN goalsaway < goalshome THEN 'L' ELSE 'T' END as away_result,	race_a.name as away_race, coach_away.pn_uname as away_coach,	
t.cas as `casualties?`, 
(g.badlyhurthome + g.serioushome + g.killshome) as "home_cas",
(g.badlyhurtaway + g.seriousaway + g.killsaway) as "away_cas",
CASE WHEN racehome = raceaway THEN 1 ELSE 0 END as mirror,
g.trhome as home_tr, traway as away_tr,
"Blood Bowl" as variant,
TRUE as swiss,
'ruleset' as ruleset,
t.tournamentstyle as style,	
t.tournamentnation as location,
CASE WHEN coach_home.oba_nation IS NULL THEN 'Old world' else coach_home.oba_nation END as home_nationality,
CASE WHEN coach_away.oba_nation IS NULL THEN 'Old world' else coach_away.oba_nation END as away_nationality,	
g.racehome as home_race_id,
g.raceaway as away_race_id
FROM naf_game g
JOIN naf_race race_h ON g.racehome = race_h.raceid 
JOIN naf_race race_a ON g.raceaway = race_a.raceid
JOIN view_coach_nation coach_home ON g.homecoachid = coach_home.coachid
JOIN view_coach_nation coach_away ON g.awaycoachid = coach_away.coachid
JOIN ( 
    SELECT nt.tournamentid, nt.tournamentstyle, nt.tournamentname, nt.tournamentnation, nt.naf_variantsid, 
    count(*) as game_count, 
    SUM(tg.badlyhurthome+tg.badlyhurtaway+tg.serioushome+tg.seriousaway+tg.killshome+tg.killsaway) as cas
    FROM naf_tournament nt
    JOIN naf_game tg ON tg.tournamentid = nt.tournamentid
    GROUP BY nt.tournamentid, nt.tournamentstyle, nt.tournamentname, nt.tournamentnation, nt.naf_variantsid
) as t ON t.tournamentid =g.tournamentid
LEFT JOIN naf_variants game_variant ON game_variant.variantid = g.naf_variantsid 
LEFT JOIN naf_variants tournament_variant ON tournament_variant.variantid = t.naf_variantsid
where (g.naf_variantsid=13 OR (t.naf_variantsid=13 AND g.naf_variantsid=0)) OR ((g.naf_variantsid=1 or t.naf_variantsid) AND g.`date` < '2021-01-01')
ORDER BY g.date ASC, g.hour ASC, g.gameid ASC
"""


def load_config(filename='naf.ini', section='mysql'):
    parser = configparser.ConfigParser()
    parser.read(filename)

    return parser[section]


def main():
    import argparse
    log_format = "[%(levelname)s:%(filename)s:%(lineno)s - %(funcName)20s ] %(message)s"
    logging.basicConfig(level=logging.INFO if "--debug" not in sys.argv else logging.DEBUG,
                        format=log_format)
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--debug', action='store_true')
    arg_parser.add_argument('--pprint', action='store_true')
    arg_parser.add_argument('--config', type=str, default='naf.ini')

    arg_parser.add_argument('datatype', type=str, choices=['all_matches', 'all_coaches'], default='all_matches')
    arg_parser.add_argument('outfile', type=argparse.FileType('w'), nargs='?', default=sys.stdout)

    arguments = arg_parser.parse_args()

    config = load_config(arguments.config)

    connection = pymysql.connect(user=config['user'],
                    password=config['password'],
                    db=config['db'],
                    host=config['host'],
                    port=int(config['port']),
                    cursorclass=pymysql.cursors.DictCursor)

    df = pd.read_sql(MATCH_QUERY if arguments.datatype == 'all_matches' else COACH_QUERY, connection)

    df.to_csv(arguments.outfile, index=False)


r = None
if __name__ == '__main__':
    r = main()
    if bool(getattr(sys, 'ps1', sys.flags.interactive)):
        print('Result of main() stored in variable r')
