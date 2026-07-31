# -*- coding: utf-8 -*-
"""부록 A 용어 사전 영어판 데이터. 렌더는 build-glossary-llm-wiki.py 가 한다."""

# (anchor, English term, Korean term, body HTML, where it shows up)
GROUPS = [
 ("layers", "The four layers",
  "The whole book runs on these four layers. Blur them into one word and the conversation goes sideways.", [
  ("taxonomy", "Taxonomy", "분류 체계",
   '''The rule that decides <strong>which drawer a note goes in</strong>. Your folder structure is your taxonomy. '''
   '''In this book that job belongs to folders like <code>Sources/10-Products/</code>. '''
   '''A drawer holds a note in one place at a time, and the limit shows up fast. Warebot is a product and at the '''
   '''same time an output of a government project, and the folder makes you pick one of the two. '''
   '''Layers 1 and 2 are what fill that gap.''',
   "Layer 0 · Chapter 3"),
  ("ontology", "Ontology", "온톨로지",
   '''<strong>The rules document that decides how notes get written.</strong> It records which kinds of things '''
   '''exist (the classes), which fields each kind must carry, and which relations may connect them. '''
   '''The most important trait is a separate one. <strong>The ontology knows nothing about your company.</strong> '''
   '''The design document goes as far as "a thing called a product exists, and a product carries '''
   '''status·owner·since" and stops there. '''
   '''The word Warebot is not in it. Neither is a revenue figure. So ask the ontology to "summarize our track '''
   '''record" and nothing comes back. It is not the kind of thing you ask. The answer comes from layer 2.''',
   "Layer 1 · Chapters 3, 8-10"),
  ("knowledge-graph", "Knowledge Graph", "지식 그래프",
   '''The format the ontology laid down, <strong>filled in with real company facts</strong>. '''
   '''Every note is a point, and every link you draw between notes is a line. This is where the answer to a '''
   '''question actually comes from. '''
   '''To answer "which technology in Warebot came out of a government project?" you follow the lines twice: '''
   '''Warebot → object recognition → the 2025 SmartLogistics project. That is what graph traversal means.''',
   "Layer 2 · Chapter 3"),
  ("llm-wiki", "LLM Wiki", "LLM Wiki",
   '''The three above plus <strong>the machinery that keeps them running with nobody tending them</strong>. '''
   '''That machinery is the rules for AI (<code>CLAUDE.md</code>), the templates, the skills, the scheduled '''
   '''tasks, the dashboard and the check scripts. '''
   '''Without it you get one well-organized folder that quietly dies three months later. '''
   '''Design the ontology and stop there, and you stop at layer 1.''',
   "Layer 3 · Chapters 3, 11-18"),
 ]),

 ("ontology-parts", "What an ontology is made of",
  "The items that actually get written into the layer 1 design document.", [
  ("class", "Class", "클래스",
   '''The <strong>kind</strong> of thing a note is. This book splits them into product, capability, project and '''
   '''opportunity. What matters is fixing one decision rule per class. '''
   '''Project and opportunity, for example, get told apart by "is there a contract or a budget attached?" '''
   '''With no rule, everyone files things differently, and then the counts come out wrong.''',
   "Chapters 3, 9"),
  ("field", "Field · Property", "필드",
   '''<strong>One property slot</strong> that a note carries. Things like <code>status</code>, <code>owner</code> '''
   '''and <code>due</code>. '''
   '''Field names have to settle on one spelling. Two hundred notes that say <code>due</code> yesterday, '''
   '''<code>deadline</code> today and <code>due_date</code> tomorrow will not turn into a Gantt chart in any tool.''',
   "Chapters 10, 15"),
  ("relation", "Relation predicate", "관계 술어",
   '''<strong>The name on the line</strong> that joins one note to another. This book names them like '''
   '''<code>pdm_uses</code> (the tech a product uses) and '''
   '''<code>pdm_output_of</code> (the project a capability came out of). '''
   '''The <code>pdm_</code> in front marks it as a predicate our own company decided on. '''
   '''Let a predicate name drift and you cannot follow the link, and then layer 2 falls apart.''',
   "Chapters 3, 10"),
  ("controlled-vocab", "Controlled Vocabulary", "통제 어휘",
   '''<strong>A list of the values you are allowed to write, settled in advance.</strong> '''
   '''A product's <code>status</code>, for example, is one of four and no more: 기획 (planned), 개발 (in '''
   '''development), 운영 (in service), 중단 (discontinued). '''
   '''Write freely instead, with entries like "nearly there" and "in progress?", and nothing can be counted. '''
   '''The point of a controlled vocabulary is not to narrow how people write. It is '''
   '''<strong>to make things countable</strong>.''',
   "Chapters 10, 17"),
  ("constraint", "Constraint", "제약",
   '''<strong>A rule that must not be broken</strong>, such as "every note carries <code>class</code>, '''
   '''<code>id</code> and <code>updated</code>". '''
   '''Do not expect people to hold to it. A check script confirms it better.''',
   "Chapters 10, 17"),
  ("identifier", "ID", "식별자",
   '''<strong>A name tag on a note that never changes.</strong> This book puts a class prefix in front, like '''
   '''<code>PRD-001</code> and <code>CAP-ObjectRecognition</code>. '''
   '''A title may change; the identifier stays put. Rename Warebot to "SmartFactoryBot" and <code>PRD-001</code> '''
   '''is still <code>PRD-001</code>, so <strong>you can still tell it is the same thing after the rename.</strong> '''
   '''What it does not do is <strong>protect the links.</strong> Links in this book are written by name, as in '''
   '''<code>[[Warebot]]</code>. Rename inside Obsidian and Obsidian rewrites the links for you; rename in Explorer '''
   '''or SharePoint and they break (Appendix C).''',
   "Chapter 9"),
  ("ssot", "SSOT · Single Source of Truth", "단일 진실 공급원",
   '''The state where the same fact is <strong>not written down differently in several places</strong>. '''
   '''Put a revenue figure in a note, in a report and on a slide, and the three drifting apart is a matter of '''
   '''time. Write it in one place and have the rest point at that place.''',
   "Chapters 10, 17"),
 ]),

 ("graph", "Words for working with the graph",
  "The names for how layer 2 produces an answer.", [
  ("node-edge", "Node · Edge", "노드와 변",
   '''<strong>The points and the lines</strong> in a graph. One note is a node, and one link from a note to '''
   '''another note is an edge. '''
   '''Write as many notes as you like: with no links there are no edges, and with no edges you have a pile of '''
   '''documents rather than a graph.''',
   "Chapter 3"),
  ("traversal", "Graph Traversal", "그래프 순회",
   '''<strong>Finding an answer by following links</strong>. '''
   '''One hop at "the tech Warebot uses", one more at "the project that tech came out of", and after two hops the '''
   '''answer is there. '''
   '''This is where answers a person could never find by searching come from, because a fact sitting two hops '''
   '''away cannot be put into a search term.''',
   "Chapter 3"),
  ("wikilink", "Wikilink", "위키링크",
   '''The notation that points at another note with two square brackets. You write it like '''
   '''<code>[[Warebot]]</code>. '''
   '''In Obsidian, writing that creates the connection for you. Every graph in this book is built on top of this '''
   '''notation.''',
   "Chapter 5"),
  ("backlink", "Backlink", "백링크",
   '''<strong>The list of notes pointing at this one.</strong> Open the Warebot note and "notes that mention '''
   '''Warebot" shows up underneath on its own. '''
   '''The good part is that it appears with nobody maintaining it. Link diligently and that much comes back to '''
   '''you for free.''',
   "Chapter 5"),
  ("moc", "Map of Content", "MOC · 지도 노트",
   '''<strong>A note that acts as the entrance</strong> into a set of other notes. Something like "All products" '''
   '''is one. '''
   '''If a folder is a drawer, an MOC is a table of contents. One note can appear in several MOCs at once, which '''
   '''is how it fills the gap a folder leaves.''',
   "Chapters 15, 16"),
 ]),

 ("tools", "Tools and files",
  "The things you actually put your hands on.", [
  ("vault", "Vault", "볼트",
   '''<strong>A single folder</strong> that Obsidian manages. When this book says "the vault", it means the '''
   '''folder holding your company knowledge. '''
   '''It is not a special format, just an ordinary folder with markdown files in it. So you can stop using '''
   '''Obsidian and the files are still there.''',
   "Chapter 5"),
  ("frontmatter", "Frontmatter", "프론트매터",
   '''<strong>The part at the very top of a markdown file, fenced by <code>---</code> lines.</strong> '''
   '''Fields like <code>class</code>, <code>status</code> and <code>owner</code> go in there. '''
   '''The body is where people read, and the frontmatter is <strong>where machines read</strong>. '''
   '''Dashboards and automation look at this part and nothing else.''',
   "Chapters 12, 15"),
  ("obsidian", "Obsidian", "옵시디언",
   '''A program that treats markdown files like a wiki. It gives you links, backlinks and a graph view. '''
   '''The important part is that it <strong>does not lock your files into its own format</strong>. '''
   '''A vault is just a folder.''',
   "Chapters 4, 5"),
  ("teams", "Microsoft Teams", "Teams",
   '''In this book it is <strong>the place people gather</strong>. Conversation happens there and decisions get '''
   '''made there. '''
   '''Conversation flows away, though, so whatever got decided has to be copied across into the vault. '''
   '''Automating that copying is one of this book's goals.''',
   "Chapter 6"),
  ("cowork", "Claude Cowork", "Claude Cowork",
   '''<strong>The hands on the AI side</strong>, reading and writing the vault. It creates notes, fixes them, and '''
   '''runs the scheduled tasks at the times you set.''',
   "Chapters 4, 7, 14"),
  ("skill", "Skill", "스킬",
   '''<strong>A document that writes down a task you repeat.</strong> Instead of explaining "make the weekly '''
   '''report" in a fresh prompt every time, you write it down once and call it by name. '''
   '''In human terms it is close to a work manual.''',
   "Chapter 13"),
  ("claude-md", "CLAUDE.md", "CLAUDE.md",
   '''<strong>The file holding the rules AI has to follow</strong> in this vault. '''
   '''Things like "do not fill in facts that are not there" and "write 확인 필요 for any number with no evidence". '''
   '''Without this file the AI makes notes in a different format every time, and fills the blanks with something '''
   '''plausible.''',
   "Chapter 11"),
  ("scheduled-task", "Scheduled task", "예약 작업",
   '''Work that <strong>runs on its own with no person involved</strong> at a set time. The check report that '''
   '''arrives every Monday morning is one. '''
   '''There is one trap. A scheduled task running remotely <strong>cannot reach a folder on your own '''
   '''computer.</strong> '''
   '''Anything that has to touch vault files has to run locally.''',
   "Chapter 14"),
 ]),

 ("ai", "Words from the AI side",
  'The words you need in order to answer "isn\'t this just RAG?"', [
  ("llm", "Large Language Model", "LLM · 대규모 언어 모델",
   '''A model trained to predict the next word. The prediction is good enough that it writes like a person. '''
   '''The key point is that <strong>it does not know what it was never taught</strong>. '''
   '''Your company's facts were never in its training, so you have to supply them separately.''',
   "Chapter 2"),
  ("rag", "Retrieval-Augmented Generation", "RAG · 검색 증강 생성",
   '''When a question arrives, <strong>you search for the relevant documents first and hand them to the AI along '''
   '''with the question</strong>. '''
   '''In this book's four-layer model, RAG is <strong>one of the ways to get an answer out of layer 2</strong> '''
   '''rather than a layer of its own. '''
   '''And RAG on its own is not enough. Search only turns up documents that look similar, and a fact sitting two '''
   '''hops away it will not find. '''
   '''That one comes out by following links.''',
   "Chapters 2, 3"),
  ("embedding", "Embedding · Vector search", "임베딩 · 벡터 검색",
   '''<strong>Turning text into a list of numbers so that things close in meaning sit close together</strong>. '''
   '''That is why searching for "revenue" turns up a document that says "earnings". '''
   '''It only finds things that are similar, though, so it does not know the <strong>exact relation</strong>. '''
   '''"Which project did this technology come out of?" is not solved by similarity.''',
   "Chapter 2"),
  ("hallucination", "Hallucination", "환각",
   '''<strong>The AI inventing a plausible fact that does not exist.</strong> It happens because a blank makes it '''
   '''want to fill the blank. '''
   '''That is why this book nails down the rule "if you do not know, write 확인 필요". '''
   '''Leaving a blank as a blank is far better.''',
   "Chapter 11"),
  ("provenance", "Provenance", "근거 · 출처",
   '''Writing down <strong>where a fact came from</strong> next to the fact itself. '''
   '''An answer with no evidence attached cannot be reviewed, because there is no way to confirm whether it is '''
   '''right or wrong. '''
   '''That is why AX maturity breaks between stage 1 and stage 3.''',
   "Chapters 11, 19"),
  ("confidence", "confidence", "confidence 필드",
   '''The slot that records <strong>how far this note can be trusted</strong>. '''
   '''<strong>There are exactly two values, <code>draft</code> and <code>reviewed</code>.</strong> '''
   '''It separates what a person has checked from what the AI drafted. '''
   '''Without this slot, reviewed facts and unreviewed facts mix together, and in the end none of them can be '''
   '''trusted.''',
   "Chapters 3, 11, 17"),
  ("context-window", "Context window", "컨텍스트 윈도우",
   '''<strong>How much the AI can look at in one go.</strong> You cannot pour the whole vault in. '''
   '''Picking out only the notes you need therefore matters, and links and fields that were put in properly make '''
   '''that picking easy.''',
   "Chapter 2"),
  ("agent", "Agent", "에이전트",
   '''An AI that does more than answer a question: it <strong>decides the order itself, uses tools, and finishes '''
   '''the job</strong>. '''
   '''It shows up at the last of the AX maturity stages. Getting there needs the evidence and the rules from the '''
   '''earlier stages already in place.''',
   "Chapter 19"),
 ]),

 ("org", "Organization and strategy",
  "The words for why you are building this system at all.", [
  ("ax", "AI Transformation", "AX · AI 전환",
   '''<strong>Bringing in</strong> AI tools and the company <strong>actually starting to work '''
   '''differently</strong> are two different things. '''
   '''The second one is AX. Buying a tool does not make it happen. How people work and how they record it have to '''
   '''change together.''',
   "Chapter 19"),
  ("ax-maturity", "AX maturity", "AX 성숙도 5단계",
   '''Stage 0 everyone on their own → stage 1 individual productivity → stage 2 shared knowledge → stage 3 built '''
   '''into the workflow → stage 4 agents. '''
   '''<strong>Skipping from stage 1 to stage 3 fails.</strong> '''
   '''Output with no evidence attached cannot be reviewed, so in the end nobody signs off on it.''',
   "Chapter 19"),
  ("trl", "Technology Readiness Level", "TRL · 기술 성숙도",
   '''A 1 to 9 scale for <strong>whether a technology is at lab level or ready to actually ship</strong>. '''
   '''It turns up often in government project paperwork. This book uses it as a field on capability notes.''',
   "Chapter 9"),
 ]),
]


CHROME = {

 "intro":
'''    <p>Come here when a word stops you mid-sentence. Only the words this book actually uses are in here, and every explanation is written <strong>to match this book's four-layer model</strong>. Some definitions will differ a little from what you find elsewhere. That is not because this book is wrong, but because every source cuts the layers differently.</p>''',

 "three_words":
'''    <div class="callout callout-tip">
      <p class="callout-title">If you only remember three words</p>
      <p><a href="#ontology" class="term-link">Ontology</a> is the <strong>rules</strong>, the <a href="#knowledge-graph" class="term-link">knowledge graph</a> is the <strong>facts</strong>, and the <a href="#llm-wiki" class="term-link">LLM Wiki</a> is <strong>the whole apparatus that keeps it all running</strong>. The moment you use the three interchangeably, the conversation goes sideways.</p>
    </div>''',

 "jump_h2": "Jump to a group",

 "count_line": "There are {total} of them. Anywhere in the book, click a word with a dotted underline and you land on its entry.",

 "where_label": "Where it shows up",

 "confusions":
'''    <h2 id="confusions">Pairs that get mixed up</h2>

    <p>Put the two words side by side and the difference gets obvious.</p>

    <table>
      <thead>
        <tr><th>This one</th><th>and this one</th><th>What is different</th></tr>
      </thead>
      <tbody>
        <tr><td>Ontology</td><td>Knowledge graph</td><td>Rules or facts. The company's name never appears once in the ontology</td></tr>
        <tr><td>Taxonomy</td><td>Ontology</td><td>Where a note goes, or how it connects. A folder gives one spot, relations give several</td></tr>
        <tr><td>Knowledge graph</td><td>LLM Wiki</td><td>Where the answer comes from, or that plus the machinery that keeps it from dying</td></tr>
        <tr><td>RAG</td><td>Graph traversal</td><td>Fetching similar documents, or following links. A fact two hops away only comes out the second way</td></tr>
        <tr><td>Folder</td><td>MOC</td><td>A drawer or a table of contents. A note goes into one drawer, but it can be listed in several tables of contents</td></tr>
        <tr><td>Note body</td><td>Frontmatter</td><td>Where people read, or where machines read. The dashboard looks at the frontmatter and nothing else</td></tr>
        <tr><td>Adopting AI</td><td>AX</td><td>You bought a tool, or the way you work changed</td></tr>
      </tbody>
    </table>

    <div class="callout callout-warning">
      <p class="callout-title">One name per field</p>
      <p>This book writes a deadline date as <code>due</code> and nothing else. It does not use <code>deadline</code> or <code>due_date</code>. Same meaning, split names, and nothing can be counted. The canonical field list is in Chapter 10.</p>
    </div>''',

 "title": "Appendix A: Glossary · Building a Company LLM Wiki",

 "meta_desc": "Ontology, knowledge graph, LLM Wiki, RAG, frontmatter and the rest of this book's vocabulary, explained plainly against the four-layer model.",

 "h1": "Glossary",

 "subtitle": "Come here when you hit a word you do not know",

 "reading_time": "Skim, about 14 min",

 "prev_href": "ch19.en.html",
 "prev_label": "← Previous: Where AX starts: the LLM Wiki",

 "next_href": "appendix-b.en.html",
 "next_label": "Next: Appendix B · Copy-paste assets →",
}
