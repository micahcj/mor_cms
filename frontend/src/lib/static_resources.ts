export type IndentValue = 'Main' | 'Bullet' | 'Sub-Bullet';
export const indentValues: IndentValue[] = ['Main', 'Bullet', 'Sub-Bullet'];

export interface TextObject {
	text: string;
	indentValue: IndentValue;
}
