Help me write a podcast script of about a 2000 words.

The "Horizon" podcast explains complicated subjects within science, technology, and current affairs. The target audience is listeners with a university degree, so people who are used to receive dense and complex information. They expects fact-based information and deep dives into subjects. The podcast does not assume deep knowledge of any particular subject, so it takes time to introduce and explain foundational concepts necessary to understand the subject matter. It also doesn't dumb down the subject but assumes that listeners will be able to follow along at a high educational level.

Make sure you thoroughly research the subject. If there has been significant development within the subject matter within recent years, be sure to compare and contrast sources and ideas to help listeners understand what has changed, and how. If a subject or concept doesn't have consensus, be sure to present multiple view points and compare and contrast. Always attribute ideas and viewpoints. If you find valuable source for information, be sure to name drop them, but do not include URLs etc. Instead, just quote the source as eg. "This idea was exclored in the October issue of Science Magazine, where ..." If the source is a person, be sure to include title and organization, eg. "Professor Johnson from CalTech".

If the subject is a historical event, be sure to include a timeline of important related events or anchor important events in other important events (eg. "Right after World War 1, ..." or "around the time of the moon landing").

Since the consumer of the podcast will only hear audio and wont read the script, it's important that challenging concepts are explained in a way that invites listeners to picture the idea in their head, and walk them through complex arguments or ideas.

The podcast should take the form of a conversation between two hosts where one host plays the role of the expert and the other asks clarifying questions. To the listener, it should feel like they have someone there in the studio asking the "stupid" or clarifying questions on their behalf. Sometimes the host playing the role of the clarifier will ask to have complex subjects explained again. The subject matter expert should then try and explain the same subject in a different way. At times the roles should be temporarily reversed so that the non-subject matter host contributes knowledge of their own, which the subject matter host then considers and continues from. eg. "I read that ...." In these cases the contributed knowledge must be factual or a common misunderstanding that is then corrected by the subject matter expert.

The two hosts are named Carl and Linda. The language of the Podcast is English. The output must be a JSON object with an episode "title" (short, without the podcast name) and a "lines" array in which every element has a "speaker" (exactly "Carl" or "Linda") and the "text" spoken. Each paragraph of speech is one element; never put speaker names inside the text. You can control the mood and delivery using the following tags: [laughs], [laughs harder], [starts laughing], [wheezing], [whispers], [sighs], [exhales], [sarcastic], [curious], [excited], [crying], [snorts], [mischievously]. It's important that you insert filler words to indicate when hosts are hesitating, thinking about how to explain something, or need a small pause to think through dense material.

You MUST not use any abbreviations such as "ie", "eg", "dr", "prof", "5x", "x4" etc. Write them out instead to ensure they are spoken correctly in the audio.

The podcast must always have the following general structure

1. Brief welcome
2. Brief introduction of the episode topic.
3. Actual episode content
4. Conclusion and round-off
5. Goodbye

The expert role for this episode is played by: ${speaker}
The subject for this episode is: ${subject}
