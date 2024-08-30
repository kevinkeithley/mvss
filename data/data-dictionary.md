# Historical data

File tournament-info.py goes through the ESPN golf leaderboard page and selects by year and tournament name and saves those values with the "tournament id" that is the last part of the url for each tournament. They are saved to .csv files by year in the data folder.

From these .csv files, we remove the tournament data for tournaments we do not want, notably any data related to match play tournaments.

## Excluded data

**Match play tournaments** 

- The Match
- Ryder Cup
- President's Cup
- WGC

**Q-School**

**Zurich Classic**

**Pro-Ams**

## Duplicated data

Due to the idiosyncrasies of the ESPN year selector including time frames like 2022-2023, there are several tournaments that get pulled in more than once.

Here are the results from 

Non-unique Tournament ID count: Tournament ID

- 401552854 -    3

- 401580329 -    2

- 401552861 -    2

- 401552859 -    2

- 401552860 -    2

- 401552858 -    2

- 401552857 -    2

- 401552856 -    2

- 401552855 -    2

Name: count, dtype: int64

Detailed information for non-unique Tournament IDs:

Tournament ID: 401552854
   Year       Tournament name                    Date                                           Location
2022-23 Fortinet Championship September 14 - 17, 2023 Silverado Resort and Spa (North Course) - Napa, CA
2022-23 Fortinet Championship September 14 - 17, 2023 Silverado Resort and Spa (North Course) - Napa, CA
2021-22 Fortinet Championship September 14 - 17, 2023 Silverado Resort and Spa (North Course) - Napa, CA

Tournament ID: 401580329
   Year Tournament name                Date                                         Location
2022-23      The Sentry January 4 - 7, 2024 Kapalua Resort (Plantation Course) - Kapalua, HI
   2024      The Sentry January 4 - 7, 2024 Kapalua Resort (Plantation Course) - Kapalua, HI

Tournament ID: 401552861
   Year      Tournament name                      Date                         Location
2022-23 Hero World Challenge Nov 30 - December 3, 2023 Albany - New Providence, Bahamas
2022-23 Hero World Challenge Nov 30 - December 3, 2023 Albany - New Providence, Bahamas

Tournament ID: 401552859
   Year                  Tournament name                  Date                                             Location
2022-23 Butterfield Bermuda Championship November 9 - 12, 2023 Port Royal Golf Course - Southampton Parish, Bermuda
2022-23 Butterfield Bermuda Championship November 9 - 12, 2023 Port Royal Golf Course - Southampton Parish, Bermuda

Tournament ID: 401552860
   Year Tournament name                   Date                                                     Location
2022-23 The RSM Classic November 16 - 19, 2023 Sea Island Resort (Seaside Course) - Saint Simons Island, GA
2022-23 The RSM Classic November 16 - 19, 2023 Sea Island Resort (Seaside Course) - Saint Simons Island, GA

Tournament ID: 401552858
   Year                    Tournament name                 Date                                         Location
2022-23 World Wide Technology Championship November 2 - 5, 2023 El Cardonal at Diamante - Cabo San Lucas, Mexico
2022-23 World Wide Technology Championship November 2 - 5, 2023 El Cardonal at Diamante - Cabo San Lucas, Mexico

Tournament ID: 401552857
   Year   Tournament name                  Date                                  Location
2022-23 ZOZO CHAMPIONSHIP October 19 - 22, 2023 Accordia Golf Narashino CC - Chiba, Japan
2022-23 ZOZO CHAMPIONSHIP October 19 - 22, 2023 Accordia Golf Narashino CC - Chiba, Japan

Tournament ID: 401552856
   Year          Tournament name                  Date                      Location
2022-23 Shriners Children's Open October 12 - 15, 2023 TPC Summerlin - Las Vegas, NV
2022-23 Shriners Children's Open October 12 - 15, 2023 TPC Summerlin - Las Vegas, NV

Tournament ID: 401552855
   Year              Tournament name                Date                              Location
2022-23 Sanderson Farms Championship October 5 - 8, 2023 Country Club of Jackson - Jackson, MS
2022-23 Sanderson Farms Championship October 5 - 8, 2023 Country Club of Jackson - Jackson, MS

# Updating data