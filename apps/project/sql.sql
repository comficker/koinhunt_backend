SELECT "project_project"."id",
       "project_project"."updated",
       "project_project"."created",
       "project_project"."db_status",
       "project_project"."verified",
       "project_project"."validation_score",
       "project_project"."init_power_target",
       "project_project"."meta",
       "project_project"."name",
       "project_project"."description",
       "project_project"."media_id",
       "project_project"."id_string",
       "project_project"."homepage",
       "project_project"."links",
       "project_project"."features",
       "project_project"."score_calculated",
       "project_project"."score_detail",
       "project_project"."main_token_id",
       "project_project"."wallet_id",
       "project_project"."nft_id",
       (SELECT U0."event_date_start"
        FROM "project_event" U0
        ORDER BY CASE
                     WHEN (U0."event_date_start" >= 2022 - 02 - 23 04:22:07.813552+00:00)
                         THEN (U0."event_date_start" - 2022 - 02 - 23 04:22:07.813552+00:00)
                     WHEN (U0."event_date_start" < 2022 - 02 - 23 04:22:07.813552+00:00)
                         THEN (2022 - 02 - 23 04:22:07.813552+00:00 - U0."event_date_start")
                     ELSE NULL END ASC
        LIMIT 1) AS "event_date_start"
FROM "project_project"
WHERE ("project_project"."db_status" = 1 AND "project_project"."wallet_id" IS NOT NULL AND
       "project_project"."validation_score" >= "project_project"."init_power_target")
ORDER BY "project_project"."score_calculated" DESC, "event_date_start" DESC
