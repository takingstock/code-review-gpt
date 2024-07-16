import { commentOnPR as commentOnPRAzdev } from "../common/ci/azdev/commentOnPR"
import { commentOnPR as commentOnPRGithub } from "../common/ci/github/commentOnPR"
import { commentPerFile } from "../common/ci/github/commentPerFile"
import { commentOnPR as commentOnPRGitlab } from "../common/ci/gitlab/commentOnPR"
import { getMaxPromptLength } from "../common/model/getMaxPromptLength"
import { PlatformOptions, type ReviewArgs, type ReviewFile } from "../common/types"
import { logger } from "../common/utils/logger"
import { signOff } from "./constants"
import { priorityReport } from "./prioritise"
import { constructPromptsArray } from "./prioritise/prompt/constructPrompt/constructPrompt"
import { filterFiles } from "./prioritise/prompt/filterFiles/index"

export const review = async (
  yargs: ReviewArgs,
  files: ReviewFile[],
  openAIApiKey: string
): Promise<void> => {
  logger.debug(`Review started.`)
  logger.debug(`Model used: ${yargs.model}`)
  logger.debug(`Ci enabled: ${yargs.ci ?? "ci is undefined"}`)
  logger.debug(`Comment per file enabled: ${String(yargs.commentPerFile)}`)
  logger.debug(`Review type chosen: ${yargs.reviewType}`)
  logger.debug(`Organization chosen: ${yargs.org ?? "organization is undefined"}`)
  logger.debug(`Remote Pull Request: ${yargs.remote ?? "remote pull request is undefined"}`)
  logger.debug(`Emoji summary enabled: ${yargs.summary}`)

  const isCi = yargs.ci
  const shouldCommentPerFile = yargs.commentPerFile
  const modelName = yargs.model
  const reviewType = yargs.reviewType
  const organization = yargs.org
  const generateSummary = yargs.summary

  const filteredFiles = filterFiles(files)

  if (filteredFiles.length === 0) {
    logger.info("No file to review, finishing review now.")

    return undefined
  }

  logger.debug(
    `Files to review after filtering: ${filteredFiles.map(file => file.fileName).toString()}`
  )

  const maxPromptLength = getMaxPromptLength(modelName)

  const prompts = constructPromptsArray(filteredFiles, maxPromptLength, reviewType)
  logger.debug(`Prompts used:\n ${prompts.toString()}`)

  const { markdownReport: report, feedbacks } = await priorityReport(
    prompts,
    modelName,
    openAIApiKey,
    organization,
    generateSummary
  )

  logger.debug(`Markdown report:\n ${report}`)

  if (isCi === PlatformOptions.GITHUB) {
    if (shouldCommentPerFile) {
      await commentPerFile(feedbacks, signOff)
    } else {
      await commentOnPRGithub(report, signOff)
    }
  }
  if (isCi === PlatformOptions.GITLAB) {
    await commentOnPRGitlab(report, signOff)
  }

  if (isCi === PlatformOptions.AZDEV) {
    await commentOnPRAzdev(report, signOff)
  }

  return
}
