SELECT "project_project"."id",
       "project_project"."updated",
       "project_project"."created",
       "project_project"."db_status",
       "project_project"."verified",
       "project_project"."validation_score",
       "project_project"."meta",
       "project_project"."name",
       "project_project"."description",
       "project_project"."media_id",
       "project_project"."id_string",
       "project_project"."homepage",
       "project_project"."links",
       "project_project"."score_calculated",
       "project_project"."score_detail",
       "project_project"."main_token_id",
       "project_project"."wallet_id",
       "project_project"."nft_id"
FROM "project_project"
WHERE ("project_project"."db_status" = 1 AND "project_project"."wallet_id" IS NOT NULL AND
       "project_project"."validation_score" >= 1000.0)
ORDER BY "project_project"."id" DESC, "project_project"."score_calculated" DESC
