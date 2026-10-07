# Corrected-sentence experiment: development comparison

The baseline judgments were approved by the project owner. Candidate results below are new actual model outputs and require their own review. Exact sentence matches do not prove explanation quality. Rejected output remains a failure, not an empty success.

| Row | Input | Baseline approved outcome | Candidate sentence | Candidate explanation | Candidate status |
|---:|---|---|---|---|---|
| 1 | I live near the station. | correct_abstention | I live near the station. | (none) | valid |
| 2 | She walk to work every morning. | useful | She walks to work every morning. | Use present simple third person singular for the verb after a subject that is a singular pronoun (she). | valid |
| 3 | Could we have separate bills, please? | correct_abstention | Could we have separate bills, please? | (none) | valid |
| 4 | I would like two sandwich, please. | useful | I would like two sandwiches, please. | Add an 's' to 'sandwich' to make it plural, and add a comma before the conjunction 'please' for proper punctuation. | valid |
| 5 | My sister and I cycle to work. | correct_abstention | My sister and I cycle to work. | (none) | valid |
| 6 | I am engineer. | missed | I am an engineer. | Add the definite article 'an' before the noun 'engineer' to form a correct adjective phrase. | valid |
| 7 | I have been a teacher for six years. | correct_abstention | I have been a teacher for six years. | (none) | valid |
| 8 | We visited the museum yesterday and buy a postcard. | useful | We visited the museum yesterday and bought a postcard. | Corrected the past tense verb 'buy' to 'bought' for consistency with the past tense context. | valid |
| 9 | There is some rice left. | correct_abstention | There is some rice left. | (none) | valid |
| 10 | This restaurant is more cheaper than the cafe. | incorrect_edit | This restaurant is cheaper than the cafe. | Use cheaper instead of more cheaper to avoid double comparison. | valid |
| 11 | I would rather stay home tonight. | correct_abstention | I would rather stay home tonight. | (none) | valid |
| 12 | I have lived here since five years. | useful | I have lived here for five years. | Use 'for' with a duration of time like 'five years'. | valid |
| 13 | I look forward to meeting you. | correct_abstention | I look forward to meeting you. | (none) | valid |
| 14 | He can speaks Spanish. | useful | He can speak Spanish. | Use 'speak' (base verb) after 'can' for the correct verb form. | valid |
| 15 | Neither option appeals to me. | correct_abstention | Neither option appeals to me. | (none) | valid |
| 16 | I am interested on photography. | useful | I am interested in photography. | Use 'in' with the preposition for interests. | valid |
| 17 | The soup tastes delicious. | correct_abstention | The soup tastes delicious. | (none) | valid |
| 18 | There are a bowl on the table. | rejected | There is a bowl on the table. | Use 'is' with singular subject 'a bowl'. | valid |
| 19 | I used to play chess after school. | correct_abstention | I used to play chess after school. | (none) | valid |
| 20 | I did not ordered dessert. | correct_edit_explanation_fails | I did not order dessert. | Use past tense 'ordered' instead of past participle 'ordered' (incorrectly used as past tense). | valid |
| 21 | My aunt drive a bus. | useful | My aunt drives a bus. | Use third person singular verb form drives for the subject aunt. | valid |
| 22 | My aunt drives a bus. | correct_abstention | My aunt drives a bus. | (none) | valid |
| 23 | The students needs more time. | useful | The students need more time. | Use plural verb 'need' with plural subject 'students'. | valid |
| 24 | The students need more time. | correct_abstention | The students need more time. | (none) | valid |
| 25 | He is an chef. | rejected | He is a chef. | Use article 'a' before the singular noun 'chef'. | valid |
| 26 | He is a chef. | correct_abstention | He is a chef. | (none) | valid |
| 27 | We saw a elephant. | useful | We saw an elephant. | Use an before vowel sounds like elephant. | valid |
| 28 | We saw an elephant. | correct_abstention | We saw an elephant. | (none) | valid |
| 29 | Last night I watch a film. | useful | Last night I watched a film. | Use past tense verb watched for the past event. | valid |
| 30 | Last night I watched a film. | correct_abstention | Last night I watched a film. | (none) | valid |
| 31 | Yesterday she bring her lunch. | useful | Yesterday she brought her lunch. | Use past tense (brought) for the verb after 'yesterday'. | valid |
| 32 | Yesterday she brought her lunch. | correct_abstention | Yesterday she brought her lunch. | (none) | valid |
| 33 | I packed four shirt. | useful | I packed four shirts. | Plural form of shirt is shirts. | valid |
| 34 | I packed four shirts. | correct_abstention | I packed four shirts. | (none) | valid |
| 35 | We need three box. | useful | We need three boxes. | Use plural noun 'boxes' for countable object 'box'. | valid |
| 36 | We need three boxes. | correct_abstention | We need three boxes. | (none) | valid |
| 37 | You should takes a break. | useful | You should take a break. | Use take with the infinitive after 'should'. | valid |
| 38 | You should take a break. | correct_abstention | You should take a break. | (none) | valid |
| 39 | They might arrives early. | correct_edit_explanation_fails | They might arrive early. | Use arrive (base form) with modal verb might. | valid |
| 40 | They might arrive early. | correct_abstention | They might arrive early. | (none) | valid |
| 41 | Does she likes tea? | correct_edit_explanation_fails | Does she like tea? | Use like with the third person singular subject she. | valid |
| 42 | Does she like tea? | correct_abstention | Does she like tea? | (none) | valid |
| 43 | He did not wrote the note. | useful | He did not write the note. | Use write instead of wrote for the simple past tense. | valid |
| 44 | He did not write the note. | correct_abstention | He did not write the note. | (none) | valid |
| 45 | This route is more shorter. | incorrect_edit | This route is shorter. | Remove the unnecessary adjective 'more' as 'shorter' already implies comparison. | valid |
| 46 | This route is shorter. | correct_abstention | This route is shorter. | (none) | valid |
| 47 | Today is more colder than Monday. | incorrect_edit | Today is colder than Monday. | Remove extra 'more' for correct comparative structure. | valid |
| 48 | Today is colder than Monday. | correct_abstention | Today is colder than Monday. | (none) | valid |
| 49 | She has worked here since two months. | useful | She has worked here for two months. | Use 'for' with a duration of time in the present perfect tense. | valid |
| 50 | She has worked here for two months. | correct_abstention | She has worked here for two months. | (none) | valid |
| 51 | They depend of public transport. | useful | They depend on public transport. | Use 'on' instead of 'of' with the preposition for public transport. | valid |
| 52 | They depend on public transport. | correct_abstention | They depend on public transport. | (none) | valid |
| 53 | I enjoy to swim. | incorrect_edit | I enjoy swimming. | Use the gerund form after 'enjoy'. | valid |
| 54 | I enjoy swimming. | correct_abstention | I enjoy swimming. | (none) | valid |
| 55 | She decided studying medicine. | rejected | She decided to study medicine. | Add 'to' after the verb 'decided' for the infinitive form. | valid |
| 56 | She decided to study medicine. | correct_abstention | She decided to study medicine. | (none) | valid |
| 57 | Please give the key to I. | rejected | Please give me the key to I. | Add 'me' to indicate the indirect object of the verb 'give'. | valid |
| 58 | Please give the key to me. | correct_abstention | Please give me the key. | The word order in the phrase 'give the key to me' is incorrect. In English, the indirect object (me) should come after the direct object (the key) when using 'give'. The correct structure is 'give me the key'. | valid |
| 59 | This is hers coat. | incorrect_edit | This is her coat. | Use her instead of hers for the possessive pronoun. | valid |
| 60 | This is her coat. | correct_abstention | This is her coat. | (none) | valid |

## Next steps for improvement

Review the candidate replacements and explanations under the approved rubric, especially cases whose baseline outcome was a failure. If joint quality improves, repeat the same frozen experiment before considering held-out validation. Never copy improved human explanations into model results before scoring.
