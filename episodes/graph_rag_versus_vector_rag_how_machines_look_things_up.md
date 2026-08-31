# Horizon

## Episode: "Graph RAG versus Vector RAG: How Machines Look Things Up"

### Subject: What is graph-RAG and how is it different from vector-RAG. What are the use cases? Can the two approaches be combined? I so, when or why would you do this?

### Hosts: Linda (expert) & Carl (clarifying questions)

---

**CARL:** Welcome to Horizon, the show where we take something complicated and slow it down until it actually makes sense. I'm Carl.

**LINDA:** And I'm Linda. Good to be back in the studio.

**CARL:** Today we are going into the plumbing of modern artificial intelligence systems. Specifically, how a chatbot looks things up. There's a technique called retrieval augmented generation, usually shortened to RAG, and over the last couple of years it has split into two rival camps: the classic approach, vector RAG, and the newer challenger, graph RAG. So, Linda, what are we actually arguing about here?

**LINDA:** [laughs] We're arguing about the difference between finding a needle in a haystack and understanding how the pieces of hay are connected. And I'd say the marketing on this ran about two years ahead of the evidence. The good news is that in 2025 and 2026 the evidence finally caught up, and it's genuinely more interesting than either sales pitch.

**CARL:** Then let's start right at the bottom. Why does a language model need to look anything up at all?

**LINDA:** Because a language model is, um, frozen. Its knowledge is baked into its weights at training time. It doesn't know your company's contract archive, it doesn't know what happened last Tuesday, and when it doesn't know something it has an unfortunate habit of inventing something plausible. The fix was proposed back in 2020, in a paper by Patrick Lewis and colleagues at what was then Facebook AI Research, together with University College London and New York University. The idea: before the model answers, go fetch relevant documents and paste them into the prompt.

**CARL:** So it's the difference between a closed-book exam and an open-book exam.

**LINDA:** Exactly that. And everything we're discussing today is a fight about one question: who is the librarian, and how does the librarian decide which pages to hand you?

**CARL:** All right. Librarian number one is vector search. Walk me through it.

**LINDA:** So, you chop your documents into chunks, maybe a few hundred words each. Then you run each chunk through an embedding model, which turns that text into a long list of numbers, a vector. Could be seven hundred and sixty-eight numbers, could be a few thousand. Now here's the part to picture: think of each of those numbers as a coordinate. With three numbers you'd have a point in a room. With a thousand numbers you have a point in a thousand-dimensional space, which nobody can visualise, but the intuition still holds. Texts that mean similar things land near each other. It's a map of meaning, and distance on that map is semantic similarity.

**CARL:** Let me try to say that back. My question gets turned into a point on the same map, and the system hands me whichever chunks of text are sitting closest to my question.

**LINDA:** That's it. Ten nearest neighbours, say, found with an approximate search index so it stays fast even over hundreds of millions of chunks. And I want to be fair to vector search, because it is genuinely brilliant. It's cheap, it's fast, it needs no schema, it handles synonyms and paraphrases beautifully. You ask about "the film with the dinosaur theme park" and it finds Jurassic Park without the word Jurassic appearing anywhere in your question.

**CARL:** So where does it fall down?

**LINDA:** Two places, mainly. First, multi-hop questions. Imagine you ask: which of our suppliers share a component with the orders that are currently delayed? No single chunk of text contains that answer. It's stitched together from a delivery report, a bill of materials, and a supplier contract. Vector search retrieves chunks that sound like your question, and, well, none of those three documents individually sounds much like it.

**CARL:** And the second?

**LINDA:** Global questions. "What are the main themes across these fifty thousand support tickets?" There is no top ten chunks that answers that, because the answer is a property of the whole corpus, not of any passage in it. Darren Edge and his colleagues at Microsoft Research made exactly this point in their April 2024 paper, From Local to Global. They call it a query-focused summarisation problem rather than a retrieval problem.

**CARL:** Which is the door that graph RAG walks through, I assume.

**LINDA:** It is. So, librarian number two. Instead of storing your documents as a cloud of points, you read them and extract a knowledge graph. Nodes are entities, people, companies, proteins, products. Edges are relationships between them: "acquired", "supplies", "inhibits", "reports to". Each little fact becomes a triple: subject, relationship, object. Then, crucially, in Microsoft's design, you run a community detection algorithm over that graph, the Leiden algorithm, which finds tightly interconnected clusters. And then you have the language model write a summary of each cluster, and summaries of clusters of clusters, all the way up.

**CARL:** Hmm. Can you try that last part again, a different way? I lost you at clusters of clusters.

**LINDA:** Sure. Picture a large organisation. If I asked you what the company is worried about this quarter, you would not read every email. You'd read the team summaries, then the department summaries, then the one-page executive brief. Graph RAG builds that hierarchy automatically, except the teams aren't the official org chart, they're discovered from the data itself, from who actually talks to whom. Then, when someone asks a broad question, the system answers it from every relevant community summary in parallel and merges those partial answers into one. Microsoft calls that global search. If instead you ask a narrow question about one entity, it does local search: find that node, walk out to its neighbours, and pull the text behind them.

**CARL:** Okay, now I can see it. Can I offer something I read? My understanding was that graph RAG basically just means swapping your vector database for a graph database.

**LINDA:** That's a really common shorthand, and it's misleading. The database is an implementation detail. Graph RAG is a retrieval strategy, and almost every serious graph system still uses embeddings inside it, to match your question to the right entities in the first place. Microsoft's own framing is elegant, actually: vector RAG is a best-first search, it goes straight to the most similar text. Graph RAG global search is a breadth-first search, it sweeps the whole dataset by structure. Different search shapes, not different vendors.

**CARL:** Here's my other objection, and, um, forgive me if it's naive. Knowledge graphs are not new. The Semantic Web people were doing this in the early two thousands, Google launched its Knowledge Graph in 2012. What changed?

**LINDA:** [excited] No, that's a great point, and you're right on the history. What changed is both ends of the pipe. Historically, building a knowledge graph meant armies of ontologists and data engineers hand-curating a schema, which is why it stayed the preserve of Google and a few pharmaceutical companies. Now a language model reads messy text and drafts the graph for you. And on the other end, a language model can consume a subgraph directly as context. So the expensive human bottleneck at both ends dissolved. The old idea got a new engine.

**CARL:** So does it work? Give me numbers.

**LINDA:** Right, and this is where you have to be careful, because it depends entirely on the question type. On broad sense-making questions, the Microsoft team reported that graph RAG beat conventional vector RAG on comprehensiveness in roughly seventy-two to eighty-three percent of head-to-head comparisons, and on diversity in about sixty-two to eighty-two percent. And their top-level community summaries answered those questions using something like ninety-seven percent fewer tokens than shoving the source text through a summariser.

**CARL:** That sounds decisive.

**LINDA:** [laughs] And then the counter-evidence arrives. There's a systematic evaluation led by Haoyu Han at Michigan State University, with collaborators from Meta and IBM Research, that ran plain RAG against four families of graph RAG under one identical protocol. Same chunking, same embeddings, same generator. And they found no single winner. On simple single-hop factual lookup, plain vector RAG edged ahead, roughly sixty-five to sixty-three. On multi-hop reasoning, graph-guided retrieval pulled in front, about seventy to sixty-seven. A more recent benchmark, GraphRAG-Bench, presented at the 2026 International Conference on Learning Representations, drew the same boundary: simple fact retrieval, text chunks win. Complex reasoning, graphs win.

**CARL:** So the graph isn't an upgrade, it's a specialisation.

**LINDA:** Beautifully put, and that's exactly the framing a recent VentureBeat piece used, under the headline "stop graphing everything". Though there is one number that keeps me on the graph side for hard questions: retrieval recall. On the standard multi-hop benchmarks, whether the correct supporting passage even makes it into the top five results climbs from around seventy-three percent with naive retrieval to around eighty-eight percent with graph-guided retrieval. On the very hardest cross-document sets the gain is thirty points or more.

**CARL:** What's the catch? Because there's always a catch.

**LINDA:** The catch, historically, was money. Building the graph means running a language model over every single document to extract entities and relationships, then a second pass to summarise every community. For a genuinely large corpus, people were quoting indexing bills around thirty-three thousand dollars in API calls. For one index. Which you then have to rebuild when the documents change.

**CARL:** [laughs] That's a hard sell to a finance department.

**LINDA:** It was. So in late 2024 the same Microsoft team, Darren Edge, Ha Trinh and Jonathan Larson, published something called LazyGraphRAG, and the name is the whole idea. Do no summarisation up front. Build only the cheap skeleton, and defer the expensive reasoning to query time, on just the slice of graph the question actually touches. Their claim is that indexing costs become identical to vector RAG, roughly a thousandth of full graph RAG, while matching global search quality at a tiny fraction of the query cost. As of last year it's been folded into their agentic science platform, Microsoft Discovery.

**CARL:** Sorry, so lazy here means "don't precompute anything you might not need"?

**LINDA:** Precisely. Like a student who doesn't summarise the whole textbook in advance, but who knows the index well enough to assemble an answer on demand. And there's a parallel line of work from the University of Hong Kong, together with Beijing University of Posts and Telecommunications, called LightRAG, which attacks the other half of the problem: incremental updates. You add a new document, you patch the graph, rather than rebuilding it from scratch.

**CARL:** Let me push back with something else I've heard. People say all of this becomes obsolete because context windows keep growing. Just paste the whole archive into the prompt.

**LINDA:** [sighs] I hear that constantly. Three problems. One, scale: a million-token window sounds enormous until you notice a mid-sized enterprise archive is billions of tokens. Two, cost and latency: you pay for every token, every time, on every query. And three, attention degrades. Models demonstrably lose track of material buried in the middle of very long inputs. And there's a fourth, which matters more than people admit: auditability. A graph gives you a traceable path, this entity, this relationship, this source document. A regulator will accept that. "The vectors were close together" is not an explanation.

**CARL:** Okay, so concretely, who should use which?

**LINDA:** Vector RAG is the default and should stay the default for: semantic search over documentation, help centres, single-fact lookups, huge and rapidly changing corpora, anything where the answer lives in one passage. It is cheap, robust, and you can ship it in a week. Reach for graphs when the question shape changes. Investigative work, fraud and money-laundering networks, where the whole point is the path between people. Supply chain dependency analysis. Regulatory impact analysis, if this clause changes, what else breaks. Biomedical research, where you're chaining gene to protein to pathway to disease across thousands of papers. And corpus-level sense-making, the "what are the emerging risks in this pile of reports" question.

**CARL:** Is there a documented case of this working in the wild, rather than on a benchmark?

**LINDA:** Yes, and it's my favourite one, because it's boring and operational. Engineers at LinkedIn published a paper in 2024 on customer service question answering. Instead of treating historical support tickets as flat text, they built a graph that preserved the structure inside each ticket and the relations between tickets. Retrieval quality improved dramatically, and after roughly six months in production, median per-issue resolution time dropped by about twenty-eight percent. That's not a benchmark score, that's support engineers going home earlier.

**CARL:** And where does graph RAG fail badly? Because I want the honest version.

**LINDA:** Entity resolution, above all. Is "Apple" the company or the fruit? Are "J. Smith", "John Smith" and "Smith, John A." one node or three? Get that wrong and you either fragment the graph into useless dust or you merge two unrelated people into a single fictional person, and then the system confidently reports relationships that never existed. Extraction errors compound in a way that similarity search errors do not, because the graph presents itself as structured truth. Plus, ontology drift, staleness, and, honestly, engineering complexity. A graph is a thing you have to maintain forever.

**CARL:** Which brings us to the question I've been waiting to ask. Can you combine them? Or is this genuinely an either-or?

**LINDA:** Combining them is not just possible, it's now the mainstream production pattern. Let me give you four flavours, roughly in order of ambition. Number one, and the simplest: the router. You put a small classifier in front, which asks, is this a lookup question or a relational question? Lookup goes to the vector index, relational goes to the graph. There's even recent work using reinforcement learning to train that routing decision, so the system learns from experience which retriever pays off for which question.

**CARL:** That feels almost too simple to count as clever.

**LINDA:** [laughs] The best engineering usually does. Number two: vectors as the front door, graph as the hallway. You use vector or keyword search to find your entry-point nodes, because matching messy human language to the right entity is exactly what embeddings are good at. Then you traverse outwards from those nodes to collect connected context. Neo4j ship this as a standard retriever in their graph RAG toolkit, hybrid search first, then a traversal step. Picture it as: semantic search tells you which door to knock on, the graph tells you who's in the rest of the house.

**CARL:** Nice. Number three?

**LINDA:** Graph as a re-ranker, which is the most elegant one intellectually. This is the HippoRAG line of work from Bernal Jiménez Gutiérrez, Professor Yu Su and colleagues at Ohio State University. Their inspiration is the hippocampal indexing theory of human memory, the idea that your neocortex stores the content while the hippocampus stores a sparse index of associations. So they run Personalized PageRank over the knowledge graph, seeded by the entities in your question, and let relevance spread through the network like water through a river delta. Passages downstream of many activated entities float to the top. The original version reported up to twenty percent better multi-hop accuracy at a fraction of the cost of iterative retrieval, but, and this is the honest bit, it got worse than plain vector search on simple factual questions.

**CARL:** Which is that same trade-off appearing again.

**LINDA:** It is, and that's why the follow-up matters. HippoRAG 2, presented at the International Conference on Machine Learning in 2025, was explicitly designed to remove that regression, by folding the passages themselves into the graph rather than keeping the graph as a separate structure. Their claim is comprehensive improvement over standard retrieval on factual, associative and sense-making tasks simultaneously. That's the direction of travel: not graph instead of vectors, but graph and vectors in one retrieval substrate.

**CARL:** And the fourth flavour?

**LINDA:** Fuse them at query time, which is essentially what LazyGraphRAG does. Best-first similarity search to find promising material, breadth-first graph structure to make sure you've covered the whole dataset, and then you spend as much reasoning budget as the question deserves. The interesting property there is that quality scales smoothly with budget. Cheap question, cheap answer. Board-level question, spend more.

**CARL:** So if I'm a technical lead with a limited budget, what's the decision procedure?

**LINDA:** Um, four questions. First: what shape are my users' questions, honestly? Log them for a month before you architect anything. If eighty percent are single-fact lookups, a graph is expensive theatre. Second: how entity-dense and relationship-heavy is my domain? Contracts, clinical records, incident tickets, yes. Marketing copy, no. Third: how stable is the corpus? Fast-churning data punishes precomputed graphs, so lean lazy or incremental. And fourth: do I need to defend the answer to an auditor? If yes, the graph's traceability may justify the cost on its own. Then build a strong vector baseline with a real evaluation set, and only add graph structure where you can measure it earning its keep.

**CARL:** Before we wrap, is there anything on the horizon, so to speak, that changes this picture again?

**LINDA:** Yes, and it's the reason this topic won't go quiet. As systems shift from answering single questions to being agents that work over days and weeks, the graph stops being a static index and becomes memory. There's a body of work on temporal knowledge graphs for agents, systems like Zep, which track not just that a fact is true but when it was true and when it stopped being true. Retrieval and memory are converging, and the graph is turning out to be a rather good substrate for both.

**CARL:** Let me try to summarise, and you correct me. Vector RAG maps text into a space of meaning and hands you the nearest passages. Fast, cheap, excellent at finding a thing. Graph RAG extracts entities and relationships, and can answer questions about how things connect, and about a whole corpus at once. Slower, pricier, harder to maintain. The benchmark evidence says neither wins outright: single-hop favours vectors, multi-hop and sense-making favour graphs. And in practice, serious systems now combine them, with a router, or vector entry points plus traversal, or the graph acting as a re-ranker over passages.

**LINDA:** I'd only add one sentence: the cost objection that killed graph RAG for most teams in 2024 has largely been engineered away by lazy indexing and incremental updates, which means the decision is now about question shape rather than budget. And, please, don't graph everything. Structure is a tool, not a virtue.

**CARL:** [laughs] Put that on a poster. Linda, thank you, that was genuinely clarifying.

**LINDA:** My pleasure, Carl.

**CARL:** That's it for this episode of Horizon. If you want to go deeper, look up the Microsoft Research paper From Local to Global, the Michigan State and Meta systematic evaluation of retrieval augmented generation versus graph retrieval, and the HippoRAG work out of Ohio State University. Thanks for listening, and we'll see you next time.

**LINDA:** Goodbye, everyone.
