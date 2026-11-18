# Benchside 0.4.4

Setup now offers **Enable all five**, **Choose specific categories**, **Decide
later**, then **Decline all**, with no recommended or preselected answer.

After the agent explains the five categories and their privacy/review terms,
an explicit all-five choice saves workflow-observation, feedback, usage,
survey-invitation and private conversation-analysis preferences together.
There is no five-question reconfirmation. General interest or a UI default is
not enough to enable all five.

This changes shared onboarding instructions across local agents, the Python
package, Claude's setup helper and all three plugin/skill archives. It does not
change runtime APIs, receiver formats, storage formats or existing permissions.
Returning researchers keep their saved choices. Conversation sources, supporting
activity-category sharing, demographics, study agreements and exact submission
approvals remain separate; setup sends nothing.

Update the local package and rerun its existing `bench setup` command, or use the
host's complete plugin/skill update flow with the matching 0.4.4 archive. Start a
fresh chat to load the revised instructions. Version 0.4.4 remains compatible with
0.4.3 stores; apps older than 0.4.3 still need the coordinated update described in
the [0.4.3 notes](release-0.4.3.md). No receiver deployment is needed.
