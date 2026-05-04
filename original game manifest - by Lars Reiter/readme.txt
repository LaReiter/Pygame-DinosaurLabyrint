Mappen her indeholder information om 2D spillet "Dinosaur Maze", et spil der skal designes i Python, men endnu ikke er programmeret.

***Spillets opbygning***
- Spillet består af 100 labyrinter der skal gennemføres sekventielt og er sorteret fra lettest (bane 1) til sværest (bane 100).
	- Spilleren starter i bane 1, og avancerer 1 niveau efter hver gennemført bane
	- De første baner består af små labyrinter 
	- De senere baner består af store labyrinter 
	- For hver bane spilleren gennemfører, stiger sværheden i næste bane: større labyrint samt stærkere og/eller flere dinosaurer; se nedenfor
	- I hver bane, kan spilleren kun se starten af labyrinten, mens resten er skjult ('fog of war') men bliver gjort synligt
efterhånden som spilleren udforsker mere af labyrinten
- Derudover består hver labyrint af én eller flere dinosaurer der bevæger sig semi-tilfældigt rundt (se næste punkter)
	- Hvis en kødædende dinosaur får øje på dig, vil den jagte dig målrettet
		- Når en kødædende dinosaurer ikke kan se dig, vil den igen gå tilfældigt rundt i Labyrinten
		- Hvis en kødædende dinosaur fanger dig, bliver du spist og taber banen.
	- Hvis en planteæder møder en t-rex, vil de kæmpe, og planteæderen taber efter en rum tid
	- Planteædere går altid tilfældigt rundt i labyrinten.

***Formål***
- I hver labyrint skal man styre sin pixel karakter fra start til slut igennem labyrinten
- Man gennemfører en bane ved at finde vejen fra start til slut, uden at blive spist af en kødædende dinsosaur

***Spilmappens (hovedmappens) indhold***

Denne spilmappe består af 3 mapper ("brachiosaurus", "player", "trex") der hver i sær består af 'frames' (.png billeder) der animerer bevægelse af spilleren og dinosaurerne i én af labyrintens retninger:
	- Billeder der slutter h1 (første "frame") og h2 (anden "frame") kan tilsammen animere en bevægelse horisontalt i labyrinten 
 (kræver en spejling afhængig af venstre/højre bevægelse)
	- Billeder der slutter u1 (første "frame") og u2 (anden "frame") kan tilsammen animere en bevægelse opad i labyrinten 
	- Billeder der slutter d1 (første "frame") og d2 (anden "frame") kan tilsammen animere en bevægelse nedad i labyrinten


Derudover består spilmappen af en mappe "environment" som indeholder statisk grafik af træer og stier, der skal bruges til at konstruere labyrinterne. Konkret indeholder mappen:
- road_flat.png (en flad sti)
- road_corner.png (en hjørne sti; en sti der buer)
- tree.png (et træ der skal bruges som vægge/blokade i labyrinten)

Endelig består spilmappen af en mappe "code example for maze generation (old game)". Denne mape indeholder et python script brugt i et tidligere spil til at generere tilfældige labyrinter. Dette kan bruges som inspiration, til at implementere dele af spillet "Dinosaur Maze", men det er ikke en nødvendighed.

/Lars Nørtoft Reiter