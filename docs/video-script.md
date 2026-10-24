# Demo video: shots and voiceover

The video (2 minutes 20 seconds, under the 3-minute limit) is rendered frame by frame from the test bench, so every
number on screen comes from `results/`. Each shot carries an on-screen caption; read the voiceover over it.

| Time | Shot | Voiceover |
| --- | --- | --- |
| 0:00 | The solar system, year 0 | We are Black Ant. We move Earth from 1 AU to 2.7 AU with a gravity tractor that light holds in place. |
| 0:10 | The Earth tow up close, year 1,200 | An asteroid of four times ten to the twenty kilograms sits 637,100 km from Earth, and its gravity pulls Earth outward. Earth pulls back just as hard, and light on the asteroid's mirror holds it in place. No beam comes within 420,000 km of Earth. |
| 0:30 | The journey, 9,000 years in 40 seconds | Mars has to move first. Its own tow sprints across Jupiter's 2:1 resonance and parks it at 3.64 AU in year 5,168. Then Earth crosses the asteroid belt, and arrives at 2.7006 AU in year 8,758, inside the 10,000-year limit. |
| 1:10 | Earth safety | Mirrors in space keep Earth's sunlight at today's level. All ten safety thresholds hold the whole way: 288 K, liquid water on 82 percent of the surface, and the Moon well inside Earth's Hill sphere. |
| 1:25 | Forces and the momentum ledger | Every force is booked with its reaction: the stations' recoil, the bounced light, the asteroids sent away. The ledger closes to 5.6 times ten to the minus 16, against the guide's limit of ten to the minus 9. |
| 1:40 | A million years later | With the tows gone, we ran the new solar system for a million years. Earth stays between 2.698 and 2.702 AU, and nothing is thrown out. |
| 1:55 | Octo-Earth | We audited the reference concept too: its arms push only on Earth's own core, and a 12,000 km arm buckles under its own weight. |
| 2:10 | Validation | All ten official benchmarks pass. The code, the report and this test bench are on GitHub. |

Re-render: start the viewer (`cd viewer && npm run dev`), then in `viewer/` run `npm i --no-save playwright-core@1.49.1` and
`node scripts/video.mjs http://localhost:5173/ frames`, and join the frames at 25 per second with ffmpeg.
