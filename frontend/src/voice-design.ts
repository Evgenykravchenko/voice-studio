export const sparkLevels=['very_low','low','moderate','high','very_high'] as const;
export type SparkLevel=typeof sparkLevels[number];
export interface SparkVoice {gender:'male'|'female';pitch:SparkLevel;speed:SparkLevel;}
export function sparkDescription(voice:SparkVoice):string {
  return `${voice.gender}, ${voice.pitch} pitch, ${voice.speed} speed`;
}
export function sparkVoice(description?:string):SparkVoice {
  const match=/^(male|female), (very_low|low|moderate|high|very_high) pitch, (very_low|low|moderate|high|very_high) speed$/.exec(description??'');
  return match?{gender:match[1] as SparkVoice['gender'],pitch:match[2] as SparkLevel,speed:match[3] as SparkLevel}:{gender:'male',pitch:'moderate',speed:'moderate'};
}
