
## Notes for Programmers

#### Differences between Basic Search and Advanced Search

Before delving into the code, I thought the only difference between these two searches was that the later give finer control over the search criteria, but it turns out they use different api calls and return slightly different results. For example isOwned is included in the advanced search results, but not in the basic search results.

What this means is that if you make changes to read some of the information returned from the library searches, you need to make sure that the information is available from both searches.

