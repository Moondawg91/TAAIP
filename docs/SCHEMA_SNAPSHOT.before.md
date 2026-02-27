# SCHEMA_SNAPSHOT.before.md
Generated: Fri Feb 27 01:00:06 UTC 2026

## Git status (porcelain)
# branch.oid 4661eeb19687ac49ed25d9fd2bbdc8d11afa58e6
# branch.head feature/taaip-usarec-assets-master
1 .M N... 100644 100644 100644 380fd3abbfe7b44fb2690bd83f7ac63121934c43 380fd3abbfe7b44fb2690bd83f7ac63121934c43 alembic/env.py
1 .M N... 100644 100644 100644 f507e159cb093a92378f59bf15b2833ef51c46ef f507e159cb093a92378f59bf15b2833ef51c46ef apps/web/build/asset-manifest.json
1 .M N... 100644 100644 100644 2e44b6689039ffd65077c327a0fce9e8af5e01cb 2e44b6689039ffd65077c327a0fce9e8af5e01cb apps/web/build/index.html
1 .D N... 100644 100644 000000 47b6a6d833e74eb6c5382493c0e0e850369cbca0 47b6a6d833e74eb6c5382493c0e0e850369cbca0 apps/web/build/static/js/main.208fdaa9.js
1 .D N... 100644 100644 000000 5fef31964d86268380dd45d820aa64493a374406 5fef31964d86268380dd45d820aa64493a374406 apps/web/build/static/js/main.208fdaa9.js.LICENSE.txt
1 .D N... 100644 100644 000000 dc6feadbe45c5cf3905f8cb117823687c175fb98 dc6feadbe45c5cf3905f8cb117823687c175fb98 apps/web/build/static/js/main.208fdaa9.js.map
1 .M N... 100644 100644 100644 9241d7fce75743c8d661115f94dab0c15870e85f 9241d7fce75743c8d661115f94dab0c15870e85f apps/web/public/index.html
1 .M N... 100644 100644 100644 bb5bae270cffc7989810a8bc8d0354e1ba820f78 bb5bae270cffc7989810a8bc8d0354e1ba820f78 apps/web/src/App.js
1 .M N... 100644 100644 100644 a4002d4a580380b1ee412701071d1287f541e744 a4002d4a580380b1ee412701071d1287f541e744 apps/web/src/api/client.js
1 .M N... 100644 100644 100644 6745c229e42af38671ae9c4fe8c811b9fa2049b9 6745c229e42af38671ae9c4fe8c811b9fa2049b9 apps/web/src/api/phoneticsClient.js
1 .M N... 100644 100644 100644 d85291fd2266a20782f737e3827f67a1f9a6e675 d85291fd2266a20782f737e3827f67a1f9a6e675 apps/web/src/components/CoverageCharts.js
1 .M N... 100644 100644 100644 5ab697774533f7bbbea92a78880eedb3bd83d085 5ab697774533f7bbbea92a78880eedb3bd83d085 apps/web/src/components/DashboardFilterBar.tsx
1 .M N... 100644 100644 100644 1675b7ec37fe5f7cc84699200cc90e85e96f7e1c 1675b7ec37fe5f7cc84699200cc90e85e96f7e1c apps/web/src/components/EmptyStateWithReadiness.jsx
1 .M N... 100644 100644 100644 cd86a2bcfa5ca67f276da70fc1306c3da8212553 cd86a2bcfa5ca67f276da70fc1306c3da8212553 apps/web/src/components/ExportMenu.tsx
1 .M N... 100644 100644 100644 d109d55131fc72ca61a95cced3dd75a0ba80c276 d109d55131fc72ca61a95cced3dd75a0ba80c276 apps/web/src/components/MaintenanceGuard.tsx
1 .M N... 100644 100644 100644 52a8ffdeefd2121d00362a826dc455a66e408c53 52a8ffdeefd2121d00362a826dc455a66e408c53 apps/web/src/components/NavSidebar.tsx
1 .M N... 100644 100644 100644 bde48cfbd87467ef7980e2b475c2a19de9c8a754 bde48cfbd87467ef7980e2b475c2a19de9c8a754 apps/web/src/components/ScopePicker.js
1 .M N... 100644 100644 100644 96326807639f19a5dfd3fc35b8e6dccc611b2814 96326807639f19a5dfd3fc35b8e6dccc611b2814 apps/web/src/components/SectionSidebar.tsx
1 .M N... 100644 100644 100644 27ad3b93caa2791efdfc36e5039ee8d116cb912a 27ad3b93caa2791efdfc36e5039ee8d116cb912a apps/web/src/components/SidebarFilters.js
1 .M N... 100644 100644 100644 50b840b08c00296581692d0679c3ece34b0026c9 50b840b08c00296581692d0679c3ece34b0026c9 apps/web/src/components/SystemStrip.jsx
1 .M N... 100644 100644 100644 7f45c704bd345c48bf418cd6ab93693c22f62386 7f45c704bd345c48bf418cd6ab93693c22f62386 apps/web/src/components/TopHeader.tsx
1 .M N... 100644 100644 100644 02f8617bb2d5ebe591429f675f097660c3df5610 02f8617bb2d5ebe591429f675f097660c3df5610 apps/web/src/components/command/CommandPrioritiesPanel.js
1 .M N... 100644 100644 100644 22598ac3c840e19bb78bf94ed380b84be6cafa8b 22598ac3c840e19bb78bf94ed380b84be6cafa8b apps/web/src/components/command/LoeEditorPanel.js
1 .M N... 100644 100644 100644 42c22e07a86cbd6017ce3fc63b2fec11f7966d81 42c22e07a86cbd6017ce3fc63b2fec11f7966d81 apps/web/src/components/command/ZeroStatePanel.js
1 .M N... 100644 100644 100644 81b217513c49226bd16e6cc9c2f4e5f83a10b4f7 81b217513c49226bd16e6cc9c2f4e5f83a10b4f7 apps/web/src/components/common/EmptyState.tsx
1 .M N... 100644 100644 100644 5f24d7698d060c1d3539106cb836dec80b0cc1f7 5f24d7698d060c1d3539106cb836dec80b0cc1f7 apps/web/src/components/dashboard/DashboardToolbar.tsx
1 .M N... 100644 100644 100644 4172513706441d897d212d5873b8771454805837 4172513706441d897d212d5873b8771454805837 apps/web/src/components/home/FlashBureauPanel.tsx
1 .M N... 100644 100644 100644 5f351e15ab5289b5020916e1e60f7942f186ceff 5f351e15ab5289b5020916e1e60f7942f186ceff apps/web/src/components/home/HomeSectionShell.tsx
1 .M N... 100644 100644 100644 5aacc2fe1f03ab7d080d9183608aa6625bc187bf 5aacc2fe1f03ab7d080d9183608aa6625bc187bf apps/web/src/components/home/MessagesPanel.tsx
1 .M N... 100644 100644 100644 fa85ad11b5db20e3d2f9b0dbe61660b7b8ab5cc0 fa85ad11b5db20e3d2f9b0dbe61660b7b8ab5cc0 apps/web/src/components/home/ReferenceRailsPanel.tsx
1 .M N... 100644 100644 100644 10f172665c52ad2657d9fc2ad80d1eb16a91beac 10f172665c52ad2657d9fc2ad80d1eb16a91beac apps/web/src/components/home/UpcomingPanel.tsx
1 .M N... 100644 100644 100644 7790f53023c2b653de1936cee059e708731c3a28 7790f53023c2b653de1936cee059e708731c3a28 apps/web/src/components/imports/DocumentUploadPanel.tsx
1 .M N... 100644 100644 100644 dc4de71b650562bbf736d8a06cd5d5d7cf3d4749 dc4de71b650562bbf736d8a06cd5d5d7cf3d4749 apps/web/src/components/imports/FoundationUploadPanel.tsx
1 .M N... 100644 100644 100644 0ee45a4bd2b8d97ccc421ccdb146dca3be87bc50 0ee45a4bd2b8d97ccc421ccdb146dca3be87bc50 apps/web/src/components/operations/MarketIntelKpiStrip.jsx
1 .M N... 100644 100644 100644 69e23726a2dbc252f547f96ee8eb2876374e309d 69e23726a2dbc252f547f96ee8eb2876374e309d apps/web/src/index.js
1 .M N... 100644 100644 100644 47835f5472ae9c9002157a53c467ee876f0c9236 47835f5472ae9c9002157a53c467ee876f0c9236 apps/web/src/layout/ShellLayout.tsx
1 .M N... 100644 100644 100644 c08d9230b6cb742a726c67c6a7b6386b72040f53 c08d9230b6cb742a726c67c6a7b6386b72040f53 apps/web/src/nav/navConfig.ts
1 .M N... 100644 100644 100644 823e8ddd5d2e16a2dd761460300cb1046c5ac90f 823e8ddd5d2e16a2dd761460300cb1046c5ac90f apps/web/src/pages/HomePage.tsx
1 .M N... 100644 100644 100644 b9fefcb86f3be6ee157d6559e520ed909dd5777e b9fefcb86f3be6ee157d6559e520ed909dd5777e apps/web/src/pages/ImportCenterPage.tsx
1 .M N... 100644 100644 100644 b958f6b6d2681cc47cae1d4df2057eaa34590ff9 b958f6b6d2681cc47cae1d4df2057eaa34590ff9 apps/web/src/pages/PlaceholderPage.jsx
1 .M N... 100644 100644 100644 f63651c8abba8888f6b694157472c8288dee25d7 f63651c8abba8888f6b694157472c8288dee25d7 apps/web/src/pages/PlaceholderPage.tsx
1 .M N... 100644 100644 100644 f5691b5c3b80a56fc2e5c720a12a81521813553a f5691b5c3b80a56fc2e5c720a12a81521813553a apps/web/src/pages/admin/DataImportsPage.jsx
1 .M N... 100644 100644 100644 3dee91dfe1021c282c006e9e5e3c5ac31a5e63ee 3dee91dfe1021c282c006e9e5e3c5ac31a5e63ee apps/web/src/pages/admin/SystemConfigPage.jsx
1 .M N... 100644 100644 100644 4bdecaa63f9011fac0c7c9f0d3db4e32c9273c71 4bdecaa63f9011fac0c7c9f0d3db4e32c9273c71 apps/web/src/pages/admin/SystemSelfCheckPage.tsx
1 .M N... 100644 100644 100644 8e6de3f0aea737fe044b7dc224ccf205456f1b25 8e6de3f0aea737fe044b7dc224ccf205456f1b25 apps/web/src/pages/budget/BudgetTrackerPage.tsx
1 .M N... 100644 100644 100644 3ba97abfb8ad0bfeee7d92d7ef9f5884c03fa848 3ba97abfb8ad0bfeee7d92d7ef9f5884c03fa848 apps/web/src/pages/budget/FundingAllocationsPage.jsx
1 .M N... 100644 100644 100644 705da10d6c7cd0459b1abea3e3f84a2f1ed5cabc 705da10d6c7cd0459b1abea3e3f84a2f1ed5cabc apps/web/src/pages/budget/RoiOverviewPage.jsx
1 .M N... 100644 100644 100644 1c197d4d074a59c5ce846314c9027c5f4b71751a 1c197d4d074a59c5ce846314c9027c5f4b71751a apps/web/src/pages/command/CommandCenterPage.js
1 .M N... 100644 100644 100644 19da4d5727c55630ca768c566d51ea9c60e50cea 19da4d5727c55630ca768c566d51ea9c60e50cea apps/web/src/pages/command/CommandCenterPage.tsx
1 .M N... 100644 100644 100644 cf8a11dd4a1be68809d09027a9b7d2c627909ff1 cf8a11dd4a1be68809d09027a9b7d2c627909ff1 apps/web/src/pages/command/FusionCellPage.tsx
1 .M N... 100644 100644 100644 830a07748f64ba4f83166611a68aef76a0b24754 830a07748f64ba4f83166611a68aef76a0b24754 apps/web/src/pages/command/IntelPage.jsx
1 .M N... 100644 100644 100644 1af878bc90280e3fd1a247a7bbcf04528d0f560a 1af878bc90280e3fd1a247a7bbcf04528d0f560a apps/web/src/pages/command/MissionAnalysisPage.tsx
1 .M N... 100644 100644 100644 4b358cd5e57443bc5d6f33e87dde77d4315b7981 4b358cd5e57443bc5d6f33e87dde77d4315b7981 apps/web/src/pages/command/MissionAssessmentPage.tsx
1 .M N... 100644 100644 100644 b11e7bab79dced9eb6904a88519de07d52490c26 b11e7bab79dced9eb6904a88519de07d52490c26 apps/web/src/pages/command/MissionPlanningPage.tsx
1 .M N... 100644 100644 100644 ca7db5879b4634753c0a2aec9e571a8b4eb8c8ea ca7db5879b4634753c0a2aec9e571a8b4eb8c8ea apps/web/src/pages/command/RecruitingOpsPage.jsx
1 .M N... 100644 100644 100644 93ecabc85b3e31875b5b011f035d47a2971bc5c8 93ecabc85b3e31875b5b011f035d47a2971bc5c8 apps/web/src/pages/command/TWGPage.tsx
1 .M N... 100644 100644 100644 78cca162c32aa4f7d4a62a9ca4bd3b3c0ba2529a 78cca162c32aa4f7d4a62a9ca4bd3b3c0ba2529a apps/web/src/pages/command/TargetingDataPage.tsx
1 .M N... 100644 100644 100644 a7c27cdbbae605e292c791040cd057805c5e0e25 a7c27cdbbae605e292c791040cd057805c5e0e25 apps/web/src/pages/command/USARECTargetingPage.tsx
1 .M N... 100644 100644 100644 aa0ee91a93ebecf8a4964667e6880581f5f6af9d aa0ee91a93ebecf8a4964667e6880581f5f6af9d apps/web/src/pages/docs/LibraryPage.tsx
1 .M N... 100644 100644 100644 def688ad0cac2116ff0002e7614ccdbf093eb033 def688ad0cac2116ff0002e7614ccdbf093eb033 apps/web/src/pages/docs/RegulationsPage.tsx
1 .M N... 100644 100644 100644 5d2b7733cc0f2e7c6ff853c6e753bdb54ba9716d 5d2b7733cc0f2e7c6ff853c6e753bdb54ba9716d apps/web/src/pages/docs/SharepointPage.tsx
1 .M N... 100644 100644 100644 861c429b9aba16226616dee9c780c9d844612e21 861c429b9aba16226616dee9c780c9d844612e21 apps/web/src/pages/insights/AnalyticsPage.tsx
1 .M N... 100644 100644 100644 4caa459973db9d9c0a38350b54c4a336095a2b86 4caa459973db9d9c0a38350b54c4a336095a2b86 apps/web/src/pages/insights/FunnelPage.tsx
1 .M N... 100644 100644 100644 7aaf9bf54bb6d85264386ce3d439a6fec2147597 7aaf9bf54bb6d85264386ce3d439a6fec2147597 apps/web/src/pages/insights/MarketIntelPage.tsx
1 .M N... 100644 100644 100644 212ffe026dee6f39c6619f8157ce32b132f8de22 212ffe026dee6f39c6619f8157ce32b132f8de22 apps/web/src/pages/operations/CbsaAnalysisPage.tsx
1 .M N... 100644 100644 100644 2007dc79bbaf3988871988620a249506d72f461b 2007dc79bbaf3988871988620a249506d72f461b apps/web/src/pages/operations/DemographicsPage.tsx
1 .M N... 100644 100644 100644 195ef4f08b7fefc9d4603b8d7d83bfbd4f88dcad 195ef4f08b7fefc9d4603b8d7d83bfbd4f88dcad apps/web/src/pages/operations/MarketIntelOverviewPage.tsx
1 .M N... 100644 100644 100644 c854b238f3c30f0490fca07cd064939def4cea06 c854b238f3c30f0490fca07cd064939def4cea06 apps/web/src/pages/operations/MarketIntelligencePage.jsx
1 .M N... 100644 100644 100644 fbf4b9bdd537f9667f3b8b962c0d8526b17bfaa6 fbf4b9bdd537f9667f3b8b962c0d8526b17bfaa6 apps/web/src/pages/operations/MarketSegmentationPage.tsx
1 .M N... 100644 100644 100644 705cfab155575a1b493c7895e6807ce44b986e09 705cfab155575a1b493c7895e6807ce44b986e09 apps/web/src/pages/operations/MissionAnalysisPage.tsx
1 .M N... 100644 100644 100644 d365ccfc416de67316a202da17c5c47b7c0ef2c6 d365ccfc416de67316a202da17c5c47b7c0ef2c6 apps/web/src/pages/operations/MissionPlanningPage.tsx
1 .M N... 100644 100644 100644 342c287b6448d2767895ac240c23af483e7d540f 342c287b6448d2767895ac240c23af483e7d540f apps/web/src/pages/operations/SamaZipPage.tsx
1 .M N... 100644 100644 100644 004ff0fc704cc1c171fab38819357300231be7e9 004ff0fc704cc1c171fab38819357300231be7e9 apps/web/src/pages/operations/TargetingDataPage.tsx
1 .M N... 100644 100644 100644 7365bbdb3e539b7d819cb02358cb959f477366c6 7365bbdb3e539b7d819cb02358cb959f477366c6 apps/web/src/pages/operations/TargetingMethodologyPage.tsx
1 .M N... 100644 100644 100644 86565cd27e8e560d1eb5afa119627f032e41d9da 86565cd27e8e560d1eb5afa119627f032e41d9da apps/web/src/pages/operations/USARECTargetingPage.js
1 .M N... 100644 100644 100644 cf8ebadf2e1b357e825a51972168c339faa487bb cf8ebadf2e1b357e825a51972168c339faa487bb apps/web/src/pages/ops/CalendarPage.tsx
1 .M N... 100644 100644 100644 764fba5e8d6a1bcd0b565ea406213df4d43706c2 764fba5e8d6a1bcd0b565ea406213df4d43706c2 apps/web/src/pages/ops/EventsPage.tsx
1 .M N... 100644 100644 100644 b6460a43b03677db2d9177f99fa50a1f63a9f1ad b6460a43b03677db2d9177f99fa50a1f63a9f1ad apps/web/src/pages/ops/FusionPage.tsx
1 .M N... 100644 100644 100644 c8f2e4d829efaeca3b5f89600f646ab304361601 c8f2e4d829efaeca3b5f89600f646ab304361601 apps/web/src/pages/ops/ProjectsPage.tsx
1 .M N... 100644 100644 100644 e7f838e54212830cbe6c92919150b0c390eea131 e7f838e54212830cbe6c92919150b0c390eea131 apps/web/src/pages/ops/RoiPage.tsx
1 .M N... 100644 100644 100644 e7b78e5a716bcb213da61cfc3d49717a2160491e e7b78e5a716bcb213da61cfc3d49717a2160491e apps/web/src/pages/ops/TWGPage.tsx
1 .M N... 100644 100644 100644 61741e154a2a2fe19da5abf67124da7ac50b856d 61741e154a2a2fe19da5abf67124da7ac50b856d apps/web/src/pages/performance/AssessmentPage.tsx
1 .M N... 100644 100644 100644 9078c3a2ea16ea29c665cdb195f367eae37f3ca9 9078c3a2ea16ea29c665cdb195f367eae37f3ca9 apps/web/src/pages/performance/FunnelMetricsPage.tsx
1 .M N... 100644 100644 100644 838c03bd5e23dcd40a684679294f56ab2ecc04bb 838c03bd5e23dcd40a684679294f56ab2ecc04bb apps/web/src/pages/performance/RecruitingAnalyticsPage.jsx
1 .M N... 100644 100644 100644 d6e6c9637426d3321509f0cbb718fdefe93c0b69 d6e6c9637426d3321509f0cbb718fdefe93c0b69 apps/web/src/pages/planning/TargetingBoardPage.tsx
1 .M N... 100644 100644 100644 9be20a8549d82269f6bbed9edd44182d31de7373 9be20a8549d82269f6bbed9edd44182d31de7373 apps/web/src/pages/projects/ProjectsEventsPage.tsx
1 .M N... 100644 100644 100644 d5a9d76cf56c94b7b11159a2501150b7c35590aa d5a9d76cf56c94b7b11159a2501150b7c35590aa apps/web/src/pages/resources/HistoricalDataPage.jsx
1 .M N... 100644 100644 100644 e01ce8bdce07e6e713d1e9e475f1827f9108d66e e01ce8bdce07e6e713d1e9e475f1827f9108d66e apps/web/src/pages/resources/HonorPage.tsx
1 .M N... 100644 100644 100644 6e08b550abfa47a35c8ad23d5bd69c47c149c077 6e08b550abfa47a35c8ad23d5bd69c47c149c077 apps/web/src/pages/resources/ManualsPage.jsx
1 .M N... 100644 100644 100644 5a652ab60b0624a4ee9408030aeb6c5ba2b9ea2c 5a652ab60b0624a4ee9408030aeb6c5ba2b9ea2c apps/web/src/pages/resources/SopsPage.jsx
1 .M N... 100644 100644 100644 2d2d94cc7ddb89a09e75db6620f3913b2ddd2875 2d2d94cc7ddb89a09e75db6620f3913b2ddd2875 apps/web/src/pages/resources/TrainingModulesPage.jsx
1 .M N... 100644 100644 100644 7f584fc8aea7e534acbaa8094fe61e1ac2c99a5f 7f584fc8aea7e534acbaa8094fe61e1ac2c99a5f apps/web/src/pages/resources/UploadsPage.jsx
1 .M N... 100644 100644 100644 6f6c40a0ae3f2af5dd40b34b1137788f18589e03 6f6c40a0ae3f2af5dd40b34b1137788f18589e03 apps/web/src/pages/resources/UserManualPage.jsx
1 .M N... 100644 100644 100644 f9454029d56726ca076663d995f6b7c02c0aa0bc f9454029d56726ca076663d995f6b7c02c0aa0bc apps/web/src/pages/school/SchoolLandingPage.tsx
1 .M N... 100644 100644 100644 5bf60ce5bacbbf72621ca501e5700b641c87580e 5bf60ce5bacbbf72621ca501e5700b641c87580e apps/web/src/pages/school/SchoolProgramPage.jsx
1 .M N... 100644 100644 100644 2a2709ab8d3ee0364c7cac3052d594a64702dd34 2a2709ab8d3ee0364c7cac3052d594a64702dd34 apps/web/src/theme/muiTheme.ts
1 .M N... 100644 100644 100644 2393132947e47420b5049d8be80318f6c4b147c8 2393132947e47420b5049d8be80318f6c4b147c8 dashboard/index.html
1 .M N... 100644 100644 100644 2bf8ffaca9b7c1b089828da23102e8e01700fb44 2bf8ffaca9b7c1b089828da23102e8e01700fb44 scripts/events_handler_debug.json
1 .M N... 100644 100644 100644 ab6a325e8172931cc90dd66ae7a47baf6447185f ab6a325e8172931cc90dd66ae7a47baf6447185f services/api/.data/imports/job_1/original.csv
1 .M N... 100644 100644 100644 f4b87f5194933ffa6a400b264fbcd615b5edd5ec f4b87f5194933ffa6a400b264fbcd615b5edd5ec services/api/app/api_ingest.py
1 .M N... 100644 100644 100644 6b17b27e364e8d4b43ece35fbf402633cfaee8d3 6b17b27e364e8d4b43ece35fbf402633cfaee8d3 services/api/app/api_org.py
1 .M N... 100644 100644 100644 9f894d27ef9945b7249b47965eaf046a8a94c072 9f894d27ef9945b7249b47965eaf046a8a94c072 services/api/app/auth.py
1 .M N... 100644 100644 100644 188861fe375542c2a6156cb6571699769667cfc4 188861fe375542c2a6156cb6571699769667cfc4 services/api/app/crud_domain.py
1 .M N... 100644 100644 100644 e77ecc1f63fd02f3f90484a88fe71f64a8d18f96 e77ecc1f63fd02f3f90484a88fe71f64a8d18f96 services/api/app/database.py
1 .M N... 100644 100644 100644 44d4470de134759b0bf3bf7904ac354dfad66fa0 44d4470de134759b0bf3bf7904ac354dfad66fa0 services/api/app/db.py
1 .M N... 100644 100644 100644 2a0d5db00016a1eb9d0cfc10cbcd17cfe45921cb 2a0d5db00016a1eb9d0cfc10cbcd17cfe45921cb services/api/app/ingest.py
1 .M N... 100644 100644 100644 b33fe130f33904e101cff7dcfc62fe7c5f99c91f b33fe130f33904e101cff7dcfc62fe7c5f99c91f services/api/app/main.py
1 .M N... 100644 100644 100644 db3a4094c4c0bec0b8291899a7c2ebfff5d06176 db3a4094c4c0bec0b8291899a7c2ebfff5d06176 services/api/app/routers/command_center.py
1 .M N... 100644 100644 100644 0971365c98a10ab33c0304957a9d54f691c322f1 0971365c98a10ab33c0304957a9d54f691c322f1 services/api/app/routers/documents.py
1 .M N... 100644 100644 100644 30f2b15a04a0dcfecb3903b5beec6f7f0c729455 30f2b15a04a0dcfecb3903b5beec6f7f0c729455 services/api/app/routers/events_dashboard.py
1 .M N... 100644 100644 100644 fec803308bb7b93a1096ac93c083c5bc8bc00f3d fec803308bb7b93a1096ac93c083c5bc8bc00f3d services/api/app/routers/import_templates.py
1 .M N... 100644 100644 100644 c73320e2e7d93b4b89e942110325698a92254729 c73320e2e7d93b4b89e942110325698a92254729 services/api/app/routers/imports.py
1 .M N... 100644 100644 100644 b285a536a33b612800661644a79653a753890274 b285a536a33b612800661644a79653a753890274 services/api/app/routers/market_intel.py
1 .M N... 100644 100644 100644 16d30291158901d79904cbbe9c09f73bdb684990 16d30291158901d79904cbbe9c09f73bdb684990 services/api/app/routers/projects_dashboard.py
1 .M N... 100644 100644 100644 87f9f33724de6b9f72bc8e07765377b6b5acb2f5 87f9f33724de6b9f72bc8e07765377b6b5acb2f5 services/api/app/routers/v1.py
1 .M N... 100644 100644 100644 f73fa95977eaf898ac598dcff029c5a487e34a97 f73fa95977eaf898ac598dcff029c5a487e34a97 services/api/app/routers/v2.py
1 .M N... 100644 100644 100644 4c315d217b73d7e2cedbfb21e107053f7a1a9edd 4c315d217b73d7e2cedbfb21e107053f7a1a9edd services/api/app/routers/v2_org.py
1 .M N... 100644 100644 100644 af04c5a7bd745ec6f0c5f83691d8125ad06fcd29 af04c5a7bd745ec6f0c5f83691d8125ad06fcd29 services/api/tests/conftest.py
1 .M N... 100644 100644 100644 3a874798904db7b76e6b2ee23a418ae71c2e5c86 3a874798904db7b76e6b2ee23a418ae71c2e5c86 services/api/tests/test_domain_burden_ratio.py
1 .M N... 100644 100644 100644 433197976932407cba732f9dfcc1635cd3d03b4f 433197976932407cba732f9dfcc1635cd3d03b4f services/api/tests/test_domain_events_rbac.py
1 .M N... 100644 100644 100644 db8e15365ca103ad8b07ba668eba8eba79e25370 db8e15365ca103ad8b07ba668eba8eba79e25370 services/api/tests/test_domain_funnel_metrics.py
1 .M N... 100644 100644 100644 a533827c8d6faad4f252a550a4bd4520f15d6c38 a533827c8d6faad4f252a550a4bd4520f15d6c38 services/api/tests/test_domain_loes_eval.py
1 .M N... 100644 100644 100644 12fef3a2f24da554315c5ff49d00f89c83e1c90c 12fef3a2f24da554315c5ff49d00f89c83e1c90c services/api/tests/test_domain_marketing_summary.py
1 .M N... 100644 100644 100644 70360b085c5124c9d64d6915bbdbb8cacf781400 70360b085c5124c9d64d6915bbdbb8cacf781400 services/api/tests/test_import_commit_flow.py
1 .M N... 100644 100644 100644 feb66d77b5184fbb75923cdecfcccf069ae24c34 feb66d77b5184fbb75923cdecfcccf069ae24c34 services/api/tests/test_imports.py
1 .M N... 100644 100644 100644 b1af8a6aaddb86fa5b7e8f638895aac6a1d43ea5 b1af8a6aaddb86fa5b7e8f638895aac6a1d43ea5 services/api/tests/test_maintenance.py
1 .M N... 100644 100644 100644 f631679d5d7c043b95b2c8d0831849d8c7e5f4fc f631679d5d7c043b95b2c8d0831849d8c7e5f4fc services/api/tests/test_rbac_access.py
1 .M N... 100644 100644 100644 d1bf578497dba235f4da94ed939c3af12c0b718d d1bf578497dba235f4da94ed939c3af12c0b718d taaip-dashboard/src/components/BulkDataUpload.tsx
1 .M N... 100644 100644 100644 7ca239146f2ea713096d06ce98f19cee28d479c5 7ca239146f2ea713096d06ce98f19cee28d479c5 taaip-dashboard/src/components/SharePointIntegration.tsx
1 .M N... 100644 100644 100644 2ff48748cb338b0f84ce41bec2ba530e10c8b678 2ff48748cb338b0f84ce41bec2ba530e10c8b678 taaip-dashboard/src/components/UniversalDataUpload.tsx
1 .M N... 100644 100644 100644 630887320b114744b9c6bd1fb8cf4fc5842475a3 630887320b114744b9c6bd1fb8cf4fc5842475a3 taaip-dashboard/src/components/UploadData.tsx
1 .M N... 100644 100644 100644 f559a76ccd1f402f06465e2c52d16b2904c46ca4 f559a76ccd1f402f06465e2c52d16b2904c46ca4 taaip_service.py
? DATA_HUB_README.md
? alembic/versions/20260225_add_school_recruiting_tables.py
? alembic/versions/20260226_add_org_unit_importer.py
? apps/web/build/static/js/main.23c705fa.js
? apps/web/build/static/js/main.23c705fa.js.LICENSE.txt
? apps/web/build/static/js/main.23c705fa.js.map
? apps/web/src/api/org.ts
? apps/web/src/components/EmptyState.tsx
? apps/web/src/components/OrgUnitCascade.tsx
? apps/web/src/components/OrgUnitPicker.jsx
? apps/web/src/components/RequireAdmin.tsx
? apps/web/src/components/UnitCascadePicker.jsx
? apps/web/src/components/UnitFilterBar.tsx
? apps/web/src/components/ZeroState.tsx
? apps/web/src/components/layout/
? apps/web/src/components/ops/
? apps/web/src/components/org/
? apps/web/src/components/ui/
? apps/web/src/contexts/AuthContext.tsx
? apps/web/src/contexts/OrgSelectionContext.jsx
? apps/web/src/contexts/UnitFilterContext.tsx
? apps/web/src/layouts/DashboardLayout.jsx
? apps/web/src/pages/OperationsPage.tsx
? apps/web/src/pages/RoiPage.tsx
? apps/web/src/pages/datahub/
? apps/web/src/pages/school/CompliancePage.jsx
? apps/web/src/pages/school/CoveragePage.jsx
? apps/web/src/pages/school/DataPage.jsx
? apps/web/src/pages/school/EventsPage.jsx
? apps/web/src/pages/school/IwPage.jsx
? apps/web/src/pages/school/LeadsPage.jsx
? apps/web/src/pages/school/OverviewPage.jsx
? apps/web/src/pages/school/RoiPage.jsx
? apps/web/src/state/
? apps/web/src/store/
? apps/web/src/theme/tokens.ts
? apps/web/src/types/
? apps/web/src/utils/csvExport.js
? apps/web/src/utils/exportCsv.js
? docs/COPILOT_PROMPT_MASTER_SPEC.md
? docs/COPILOT_PROMPT_USAREC_ASSETS.md
? docs/ROUTES_SNAPSHOT.before.json
? docs/SCHEMA_SNAPSHOT.before.md
? scripts/insert_canonical_org.py
? services/api/.data/imports/job_1/original.md
? services/api/.data/imports/job_2/original.md
? services/api/.data/test_units.csv
? services/api/.data/usarec_master_units.csv
? services/api/.data/usarec_master_units_canonical.csv
? services/api/.data/usarec_master_units_normalized.csv
? services/api/app/importers/
? services/api/app/ingest_registry.py
? services/api/app/routers/auth_status.py
? services/api/app/routers/compat_importers.py
? services/api/app/routers/datahub.py
? services/api/app/routers/metrics.py
? services/api/app/routers/roi.py
? services/api/app/routers/school.py
? services/api/app/routers/school_recruiting.py
? services/api/app/routers/tasks_compat.py
? services/api/app/routers/uploads.py
? services/api/db/
? services/api/importers/
? services/api/scripts/README.md
? services/api/scripts/backfill_unit_key.py
? services/api/scripts/import_org_units.py
? services/api/scripts/seed_demo_metrics.py
? services/api/scripts/seed_metric_def.py
? services/api/tests/test_commit_compat.py
? services/api/tests/test_ingest.py
? taaip_dev.db.lock

## Alembic versions (if any)
0001_initial_schema.py
0002_phase2_domain.py
0003_timekeeping_add_columns.py
0004_fix_loemetric_and_funnelstage_timestamps.py
20260225_add_school_recruiting_tables.py
20260226_add_org_unit_importer.py
__pycache__

## CREATE TABLE occurrences (grep)
services/api/app/routers/compat_helpers.py:19:        CREATE TABLE IF NOT EXISTS audit_log (
services/api/app/routers/compat_helpers.py:51:        CREATE TABLE IF NOT EXISTS project (
services/api/app/routers/roi.py:17:    cur.execute('''CREATE TABLE IF NOT EXISTS roi_result (
services/api/app/routers/roi.py:34:    cur.execute('''CREATE TABLE IF NOT EXISTS conversion_benchmark (
services/api/app/routers/system.py:248:            CREATE TABLE IF NOT EXISTS usarec_completion (
services/api/app/routers/system.py:368:                CREATE TABLE IF NOT EXISTS maintenance_flags (
services/api/app/routers/system.py:478:    CREATE TABLE IF NOT EXISTS system_settings (
services/api/app/routers/system.py:484:    CREATE TABLE IF NOT EXISTS system_observations (
services/api/app/routers/system.py:492:    CREATE TABLE IF NOT EXISTS change_proposals (
services/api/app/routers/system.py:504:    CREATE TABLE IF NOT EXISTS change_reviews (
services/api/app/routers/system.py:513:    CREATE TABLE IF NOT EXISTS release_notes (
services/api/app/routers/command_center.py:234:                    CREATE TABLE IF NOT EXISTS loes (
services/api/app/routers/tasks.py:47:                CREATE TABLE IF NOT EXISTS tasks (
services/api/app/routers/tasks.py:59:                CREATE TABLE IF NOT EXISTS task (
services/api/app/routers/tasks.py:325:            CREATE TABLE IF NOT EXISTS task_comment (
services/api/app/routers/tasks.py:379:            CREATE TABLE IF NOT EXISTS task_assignment (
services/api/app/routers/rbac.py:179:        CREATE TABLE IF NOT EXISTS audit_log (
services/api/app/routers/v2.py:32:    cur.execute("CREATE TABLE IF NOT EXISTS surveys(id INTEGER PRIMARY KEY AUTOINCREMENT, survey_id TEXT, lead_id TEXT, responses_json TEXT, created_at TEXT)")
services/api/app/routers/v2.py:82:    cur.execute('CREATE TABLE IF NOT EXISTS external_census(id INTEGER PRIMARY KEY AUTOINCREMENT, geography_code TEXT, attributes_json TEXT, created_at TEXT)')
services/api/app/routers/v2.py:93:    cur.execute('CREATE TABLE IF NOT EXISTS external_social(id INTEGER PRIMARY KEY AUTOINCREMENT, external_id TEXT, handle TEXT, signals_json TEXT, created_at TEXT)')
services/api/app/routers/v2.py:669:        CREATE TABLE IF NOT EXISTS loe_metrics (
services/api/app/routers/v2.py:711:    cur.execute('CREATE TABLE IF NOT EXISTS loes(id TEXT PRIMARY KEY, scope_type TEXT, scope_value TEXT, title TEXT, description TEXT, created_by TEXT, created_at TEXT)')
services/api/app/routers/boards.py:23:        CREATE TABLE IF NOT EXISTS board (
services/api/app/routers/boards.py:31:        CREATE TABLE IF NOT EXISTS board_session (
services/api/app/routers/boards.py:40:        CREATE TABLE IF NOT EXISTS board_metric_snapshot (
services/api/app/routers/tactical_rollups.py:805:            CREATE TABLE IF NOT EXISTS loe_metric_map (
services/api/app/db.py:272:            CREATE TABLE IF NOT EXISTS org_unit (
services/api/app/db.py:288:            CREATE TABLE IF NOT EXISTS users (
services/api/app/db.py:299:            CREATE TABLE IF NOT EXISTS roles (
services/api/app/db.py:306:            CREATE TABLE IF NOT EXISTS user_roles (
services/api/app/db.py:314:            CREATE TABLE IF NOT EXISTS commands (
services/api/app/db.py:321:            CREATE TABLE IF NOT EXISTS import_job (
services/api/app/db.py:335:            CREATE TABLE IF NOT EXISTS import_job_preview (
services/api/app/db.py:343:            CREATE TABLE IF NOT EXISTS imported_rows (
services/api/app/db.py:352:            CREATE TABLE IF NOT EXISTS ingest_file (
services/api/app/db.py:362:            CREATE TABLE IF NOT EXISTS ingest_run (
services/api/app/db.py:374:            CREATE TABLE IF NOT EXISTS ingest_row_error (
services/api/app/db.py:383:            CREATE TABLE IF NOT EXISTS stg_raw_dataset (
services/api/app/db.py:390:            CREATE TABLE IF NOT EXISTS stg_raw_dataset_profile (
services/api/app/db.py:399:            CREATE TABLE IF NOT EXISTS import_file (
services/api/app/db.py:409:            CREATE TABLE IF NOT EXISTS import_run (
services/api/app/db.py:428:            CREATE TABLE IF NOT EXISTS import_row_error (
services/api/app/db.py:438:            CREATE TABLE IF NOT EXISTS emm_event (
services/api/app/db.py:459:            CREATE TABLE IF NOT EXISTS emm_mac (
services/api/app/db.py:468:            CREATE TABLE IF NOT EXISTS g2_market_metric (
services/api/app/db.py:482:            CREATE TABLE IF NOT EXISTS alrl_school (
services/api/app/db.py:499:            CREATE TABLE IF NOT EXISTS fstsm_metric (
services/api/app/db.py:509:            CREATE TABLE IF NOT EXISTS aie_lead_stub (
services/api/app/db.py:520:            CREATE TABLE IF NOT EXISTS fact_enlistments (
services/api/app/db.py:532:            CREATE TABLE IF NOT EXISTS fact_productivity (
services/api/app/db.py:544:            CREATE TABLE IF NOT EXISTS fact_zip_potential (
services/api/app/db.py:556:            CREATE TABLE IF NOT EXISTS fact_school_contacts (
services/api/app/db.py:572:            CREATE TABLE IF NOT EXISTS fact_school_contracts (
services/api/app/db.py:585:            CREATE TABLE IF NOT EXISTS fact_alrl (
services/api/app/db.py:596:            CREATE TABLE IF NOT EXISTS fact_mission_category (
services/api/app/db.py:608:            CREATE TABLE IF NOT EXISTS fact_emm (
services/api/app/db.py:623:            CREATE TABLE IF NOT EXISTS audit_log (
services/api/app/db.py:633:            CREATE TABLE IF NOT EXISTS event (
services/api/app/db.py:656:            CREATE TABLE IF NOT EXISTS market_zip_metrics (
services/api/app/db.py:680:            CREATE TABLE IF NOT EXISTS market_cbsa_metrics (
services/api/app/db.py:701:            CREATE TABLE IF NOT EXISTS schools (
services/api/app/db.py:715:            CREATE TABLE IF NOT EXISTS school_accounts (
services/api/app/db.py:729:            CREATE TABLE IF NOT EXISTS school_contacts (
services/api/app/db.py:740:            CREATE TABLE IF NOT EXISTS school_activities (
services/api/app/db.py:752:            CREATE TABLE IF NOT EXISTS school_milestones (
services/api/app/db.py:762:            CREATE TABLE IF NOT EXISTS school_program_leads (
services/api/app/db.py:771:            CREATE TABLE IF NOT EXISTS market_demographics (
services/api/app/db.py:788:            CREATE TABLE IF NOT EXISTS data_upload (
services/api/app/db.py:801:            CREATE TABLE IF NOT EXISTS lead_journey_fact (
services/api/app/db.py:822:            CREATE TABLE IF NOT EXISTS event_fact (
services/api/app/db.py:837:            CREATE TABLE IF NOT EXISTS spend_fact (
services/api/app/db.py:847:            CREATE TABLE IF NOT EXISTS roi_thresholds (
services/api/app/db.py:855:            CREATE TABLE IF NOT EXISTS geo_target_zones (
services/api/app/db.py:870:            CREATE TABLE IF NOT EXISTS geo_target_zone_members (
services/api/app/db.py:879:            CREATE TABLE IF NOT EXISTS market_sama_zip_fact (
services/api/app/db.py:907:            CREATE TABLE IF NOT EXISTS market_cbsa_fact (
services/api/app/db.py:928:            CREATE TABLE IF NOT EXISTS market_demographics_fact (
services/api/app/db.py:945:            CREATE TABLE IF NOT EXISTS market_zip_fact (
services/api/app/db.py:967:            CREATE TABLE IF NOT EXISTS market_cbsa_fact (
services/api/app/db.py:984:            CREATE TABLE IF NOT EXISTS school_fact (
services/api/app/db.py:1004:            CREATE TABLE IF NOT EXISTS schools (
services/api/app/db.py:1019:            CREATE TABLE IF NOT EXISTS school_zone_assignments (
services/api/app/db.py:1027:            CREATE TABLE IF NOT EXISTS school_contacts (
services/api/app/db.py:1039:            CREATE TABLE IF NOT EXISTS school_milestones (
services/api/app/db.py:1049:            CREATE TABLE IF NOT EXISTS cep_fact (
services/api/app/db.py:1064:            CREATE TABLE IF NOT EXISTS geo_campaign_fact (
services/api/app/db.py:1082:            CREATE TABLE IF NOT EXISTS market_geotarget_zone (
services/api/app/db.py:1098:            CREATE TABLE IF NOT EXISTS market_category_rule (
services/api/app/db.py:1108:            CREATE TABLE IF NOT EXISTS market_target_list (
services/api/app/db.py:1121:            CREATE TABLE IF NOT EXISTS mi_dataset_registry (
services/api/app/db.py:1130:            CREATE TABLE IF NOT EXISTS mi_import_template (
services/api/app/db.py:1141:            CREATE TABLE IF NOT EXISTS regulatory_references (
services/api/app/db.py:1152:            CREATE TABLE IF NOT EXISTS regulatory_traceability (
services/api/app/db.py:1165:            CREATE TABLE IF NOT EXISTS module_registry (
services/api/app/db.py:1208:            CREATE TABLE IF NOT EXISTS mi_zip_fact (
services/api/app/db.py:1229:            CREATE TABLE IF NOT EXISTS mi_cbsa_fact (
services/api/app/db.py:1250:            CREATE TABLE IF NOT EXISTS mi_mission_category_ref (
services/api/app/db.py:1259:            CREATE TABLE IF NOT EXISTS mi_enlistments_bde (
services/api/app/db.py:1268:            CREATE TABLE IF NOT EXISTS mi_enlistments_bn (
services/api/app/db.py:1278:            CREATE TABLE IF NOT EXISTS school_program_fact (
services/api/app/db.py:1297:            CREATE TABLE IF NOT EXISTS documents (
services/api/app/db.py:1321:            CREATE TABLE IF NOT EXISTS phonetic_map (
services/api/app/db.py:1330:            CREATE TABLE IF NOT EXISTS phonetic_dataset_registry (
services/api/app/db.py:1339:            CREATE TABLE IF NOT EXISTS home_flash_items (
services/api/app/db.py:1350:            CREATE TABLE IF NOT EXISTS home_messages (
services/api/app/db.py:1359:            CREATE TABLE IF NOT EXISTS home_recognition (
services/api/app/db.py:1369:            CREATE TABLE IF NOT EXISTS home_upcoming (
services/api/app/db.py:1379:            CREATE TABLE IF NOT EXISTS home_reference_rails (
services/api/app/db.py:1387:            CREATE TABLE IF NOT EXISTS market_taxonomy (
services/api/app/db.py:1394:            CREATE TABLE IF NOT EXISTS geo_planning_container (
services/api/app/db.py:1424:            CREATE TABLE IF NOT EXISTS project_event_link (
services/api/app/db.py:1433:            CREATE TABLE IF NOT EXISTS event_metrics (
services/api/app/db.py:1447:            CREATE TABLE IF NOT EXISTS event_plan (
services/api/app/db.py:1461:            CREATE TABLE IF NOT EXISTS event_risk (
services/api/app/db.py:1476:            CREATE TABLE IF NOT EXISTS event_roi (
services/api/app/db.py:1489:            CREATE TABLE IF NOT EXISTS event_aar (
services/api/app/db.py:1502:            CREATE TABLE IF NOT EXISTS marketing_activities (
services/api/app/db.py:1521:            CREATE TABLE IF NOT EXISTS leads (
services/api/app/db.py:1535:            CREATE TABLE IF NOT EXISTS budgets (
services/api/app/db.py:1549:            CREATE TABLE IF NOT EXISTS fy_budget (
services/api/app/db.py:1558:            CREATE TABLE IF NOT EXISTS budget_line_item (
services/api/app/db.py:1583:            CREATE TABLE IF NOT EXISTS events (
services/api/app/db.py:1597:            CREATE TABLE IF NOT EXISTS funnel_transitions (
services/api/app/db.py:1608:            CREATE TABLE IF NOT EXISTS surveys (
services/api/app/db.py:1616:            CREATE TABLE IF NOT EXISTS external_census (
services/api/app/db.py:1623:            CREATE TABLE IF NOT EXISTS external_social (
services/api/app/db.py:1631:            CREATE TABLE IF NOT EXISTS loe (
services/api/app/db.py:1641:            CREATE TABLE IF NOT EXISTS loes (
services/api/app/db.py:1651:            CREATE TABLE IF NOT EXISTS command_priorities (
services/api/app/db.py:1661:            CREATE TABLE IF NOT EXISTS priority_loe (
services/api/app/db.py:1670:            CREATE TABLE IF NOT EXISTS import_job_v3 (
services/api/app/db.py:1686:            CREATE TABLE IF NOT EXISTS import_file (
services/api/app/db.py:1695:            CREATE TABLE IF NOT EXISTS import_column_map (
services/api/app/db.py:1703:            CREATE TABLE IF NOT EXISTS import_mapping_template (
services/api/app/db.py:1712:            CREATE TABLE IF NOT EXISTS import_error (
services/api/app/db.py:1721:            CREATE TABLE IF NOT EXISTS dim_org_unit (
services/api/app/db.py:1733:            CREATE TABLE IF NOT EXISTS dim_time (
services/api/app/db.py:1742:            CREATE TABLE IF NOT EXISTS fact_production (
services/api/app/db.py:1755:            CREATE TABLE IF NOT EXISTS fact_funnel (
services/api/app/db.py:1770:            CREATE TABLE IF NOT EXISTS fact_marketing (
services/api/app/db.py:1789:            CREATE TABLE IF NOT EXISTS mission_assessments (
services/api/app/db.py:1801:            CREATE TABLE IF NOT EXISTS projects (
services/api/app/db.py:1815:            CREATE TABLE IF NOT EXISTS user_preferences (
services/api/app/db.py:1826:            CREATE TABLE IF NOT EXISTS project (
services/api/app/db.py:1842:            CREATE TABLE IF NOT EXISTS tasks (
services/api/app/db.py:1857:            CREATE TABLE IF NOT EXISTS meeting_minutes (
services/api/app/db.py:1868:            CREATE TABLE IF NOT EXISTS action_items (
services/api/app/db.py:1881:            CREATE TABLE IF NOT EXISTS task (
services/api/app/db.py:1892:            CREATE TABLE IF NOT EXISTS task_comment (
services/api/app/db.py:1900:            CREATE TABLE IF NOT EXISTS task_assignment (
services/api/app/db.py:1908:            CREATE TABLE IF NOT EXISTS calendar_events (
services/api/app/db.py:1921:            CREATE TABLE IF NOT EXISTS board (
services/api/app/db.py:1930:            CREATE TABLE IF NOT EXISTS board_session (
services/api/app/db.py:1940:            CREATE TABLE IF NOT EXISTS board_metric_snapshot (
services/api/app/db.py:1949:            CREATE TABLE IF NOT EXISTS calendar_event (
services/api/app/db.py:1968:            CREATE TABLE IF NOT EXISTS doc_library (
services/api/app/db.py:1980:            CREATE TABLE IF NOT EXISTS lms_courses (
services/api/app/db.py:1986:            CREATE TABLE IF NOT EXISTS lms_enrollments (
services/api/app/db.py:1996:            CREATE TABLE IF NOT EXISTS announcement (
services/api/app/db.py:2007:            CREATE TABLE IF NOT EXISTS system_update (
services/api/app/db.py:2015:            CREATE TABLE IF NOT EXISTS resource_link (
services/api/app/db.py:2024:            CREATE TABLE IF NOT EXISTS home_alerts (
services/api/app/db.py:2038:            CREATE TABLE IF NOT EXISTS home_flashes (
services/api/app/db.py:2050:            CREATE TABLE IF NOT EXISTS home_upcoming (
services/api/app/db.py:2062:            CREATE TABLE IF NOT EXISTS home_recognition (
services/api/app/db.py:2074:            CREATE TABLE IF NOT EXISTS home_references (
services/api/app/db.py:2085:            CREATE TABLE IF NOT EXISTS loe_metrics (
services/api/app/db.py:2103:            CREATE TABLE IF NOT EXISTS burden_snapshots (
services/api/app/db.py:2115:            CREATE TABLE IF NOT EXISTS processing_metrics (
services/api/app/db.py:2130:            CREATE TABLE IF NOT EXISTS burden_inputs (
services/api/app/db.py:2141:            CREATE TABLE IF NOT EXISTS doc_library_item (
services/api/app/db.py:2154:            CREATE TABLE IF NOT EXISTS doc_blob (
services/api/app/db.py:2166:            CREATE TABLE IF NOT EXISTS automation_job (
services/api/app/db.py:2194:                    CREATE TABLE IF NOT EXISTS marketing_activities_new (
services/api/app/db.py:2272:            cur.execute('CREATE TABLE IF NOT EXISTS funnel_stages (id TEXT PRIMARY KEY, name TEXT, rank INTEGER, created_at TEXT)')
services/api/app/db.py:2295:            CREATE TABLE IF NOT EXISTS maintenance_schedules (
services/api/app/db.py:2306:            CREATE TABLE IF NOT EXISTS maintenance_runs (
services/api/app/db.py:2355:                        CREATE TABLE IF NOT EXISTS burden_inputs_new (
services/api/app/db.py:2569:            CREATE TABLE IF NOT EXISTS expenses (
services/api/app/db.py:2718:                    # Use CREATE TABLE IF NOT EXISTS to be idempotent
services/api/app/db.py:2720:                    CREATE TABLE IF NOT EXISTS outcomes (
services/api/app/db.py:2734:                    CREATE TABLE IF NOT EXISTS outcomes (
services/api/app/db.py:2763:                CREATE TABLE IF NOT EXISTS funding_sources (
services/api/app/db.py:2783:                    CREATE TABLE IF NOT EXISTS loe_metric_map (
services/api/app/db.py:2842:                    CREATE TABLE IF NOT EXISTS marketing_activities_new (
services/api/app/db.py:2880:                CREATE TABLE IF NOT EXISTS zip_metrics (
services/api/app/db.py:2922:                    CREATE TABLE IF NOT EXISTS events_new (
services/api/app/db.py:3009:            CREATE TABLE IF NOT EXISTS market_zip_fact (
services/api/app/db.py:3027:            CREATE TABLE IF NOT EXISTS market_cbsa_fact (
services/api/app/db.py:3043:            CREATE TABLE IF NOT EXISTS market_targets (
services/api/app/db.py:3057:            CREATE TABLE IF NOT EXISTS market_rules (
services/api/app/db.py:3070:            CREATE TABLE IF NOT EXISTS mi_zip_fact (
services/api/app/db.py:3096:            CREATE TABLE IF NOT EXISTS mi_cbsa_fact (
services/api/app/db.py:3121:            CREATE TABLE IF NOT EXISTS mi_demo_fact (
services/api/app/db.py:3132:            CREATE TABLE IF NOT EXISTS mi_school_fact (
services/api/app/db.py:3214:            CREATE TABLE IF NOT EXISTS change_proposals (
services/api/app/db.py:3229:            CREATE TABLE IF NOT EXISTS api_error_log (
services/api/app/db.py:3241:            CREATE TABLE IF NOT EXISTS maintenance_flags (
services/api/app/db.py:3273:            CREATE TABLE IF NOT EXISTS audit_logs (
services/api/app/db.py:3293:            CREATE TABLE IF NOT EXISTS security_roles (
services/api/app/db.py:3300:            CREATE TABLE IF NOT EXISTS user_roles (
services/api/app/db.py:3314:            CREATE TABLE IF NOT EXISTS usarec_completion (
services/api/importers/registry.py:75:        cur.execute('''CREATE TABLE IF NOT EXISTS staging_upload(id TEXT PRIMARY KEY, filename TEXT, content_type TEXT, size_bytes INTEGER, sha256 TEXT, source_system TEXT, detected_dataset_id TEXT, detected_confidence REAL, status TEXT, error_code TEXT, error_message TEXT, created_at TEXT, imported_at TEXT)''')
services/api/importers/registry.py:76:        cur.execute('''CREATE TABLE IF NOT EXISTS staging_reject(id TEXT PRIMARY KEY, upload_id TEXT, dataset_id TEXT, row_number INTEGER, reason_code TEXT, reason_message TEXT, raw_row_json TEXT)''')
services/api/importers/datasets/g2_enlistments_bn.py:26:        cur.execute('''CREATE TABLE IF NOT EXISTS g2_enlistments_bn(id TEXT PRIMARY KEY, upload_id TEXT, unit_key TEXT, rsid TEXT, bn_display TEXT, enlistments INTEGER, report_date TEXT, ingested_at TEXT)''')
services/api/tests/test_maintenance.py:18:            CREATE TABLE IF NOT EXISTS maintenance_schedules (
services/api/tests/test_maintenance.py:28:            CREATE TABLE IF NOT EXISTS maintenance_runs (
services/api/tests/conftest.py:63:                    CREATE TABLE IF NOT EXISTS marketing_activities_new (
services/api/tests/test_import_commit_flow.py:29:            CREATE TABLE IF NOT EXISTS import_job_v3 (
services/api/tests/test_import_commit_flow.py:44:            CREATE TABLE IF NOT EXISTS imported_rows (
services/api/tests/test_import_commit_flow.py:51:            CREATE TABLE IF NOT EXISTS import_column_map (
services/api/tests/test_import_commit_flow.py:57:            CREATE TABLE IF NOT EXISTS import_file (
services/api/tests/test_import_commit_flow.py:65:            CREATE TABLE IF NOT EXISTS fact_production (
services/api/tests/test_budget_dashboard.py:41:    CREATE TABLE IF NOT EXISTS org_unit (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, type TEXT, created_at TEXT);
services/api/tests/test_budget_dashboard.py:42:    CREATE TABLE IF NOT EXISTS fy_budget (id INTEGER PRIMARY KEY AUTOINCREMENT, org_unit_id INTEGER, fy INTEGER, total_allocated REAL, created_at TEXT);
services/api/tests/test_budget_dashboard.py:43:    CREATE TABLE IF NOT EXISTS budget_line_item (id INTEGER PRIMARY KEY AUTOINCREMENT, fy_budget_id INTEGER, qtr INTEGER, event_id INTEGER, category TEXT, amount REAL, status TEXT, created_at TEXT);
services/api/tests/test_budget_dashboard.py:44:    CREATE TABLE IF NOT EXISTS projects (project_id TEXT PRIMARY KEY, title TEXT, org_unit_id INTEGER, fy INTEGER, planned_cost REAL, created_at TEXT);
services/api/tests/test_budget_dashboard.py:45:    CREATE TABLE IF NOT EXISTS event (id INTEGER PRIMARY KEY AUTOINCREMENT, org_unit_id INTEGER, name TEXT, fy INTEGER, planned_cost REAL, created_at TEXT);
services/api/tests/test_budget_dashboard.py:46:    CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT, event_id INTEGER, fy INTEGER, qtr INTEGER, org_unit_id INTEGER, amount REAL, created_at TEXT);
services/api/tests/test_rollups.py:38:    CREATE TABLE IF NOT EXISTS org_unit (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, type TEXT, created_at TEXT);
services/api/tests/test_rollups.py:39:    CREATE TABLE IF NOT EXISTS projects (project_id TEXT PRIMARY KEY, title TEXT, org_unit_id INTEGER, fy INTEGER, planned_cost REAL, created_at TEXT);
services/api/tests/test_rollups.py:40:    CREATE TABLE IF NOT EXISTS event (id INTEGER PRIMARY KEY AUTOINCREMENT, org_unit_id INTEGER, name TEXT, fy INTEGER, planned_cost REAL, project_id TEXT, created_at TEXT);
services/api/tests/test_rollups.py:41:    CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT, event_id INTEGER, fy INTEGER, qtr INTEGER, org_unit_id INTEGER, amount REAL, created_at TEXT);
services/api/tests/test_rollups.py:42:    CREATE TABLE IF NOT EXISTS fy_budget (id INTEGER PRIMARY KEY AUTOINCREMENT, org_unit_id INTEGER, fy INTEGER, total_allocated REAL, created_at TEXT);
services/api/tests/test_rollups.py:43:    CREATE TABLE IF NOT EXISTS budget_line_item (id INTEGER PRIMARY KEY AUTOINCREMENT, fy_budget_id INTEGER, qtr INTEGER, event_id INTEGER, category TEXT, amount REAL, status TEXT, created_at TEXT);
services/api/db/warehouse_schema.sql:6:CREATE TABLE IF NOT EXISTS dim_unit (
services/api/db/warehouse_schema.sql:15:CREATE TABLE IF NOT EXISTS dim_date (
services/api/db/warehouse_schema.sql:23:CREATE TABLE IF NOT EXISTS staging_uploads (
services/api/db/warehouse_schema.sql:32:CREATE TABLE IF NOT EXISTS metric_definition (
services/api/db/warehouse_schema.sql:39:CREATE TABLE IF NOT EXISTS fact_funnel_daily (

## SQL / model files mentioning CREATE TABLE or table definitions
