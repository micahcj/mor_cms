// static_resources.ts

// Indent levels
export type IndentValue = 'Main' | 'Bullet' | 'Sub-Bullet';
export const indentValues: IndentValue[] = ['Main', 'Bullet', 'Sub-Bullet'];

// Tree node for nested list
export interface TreeNode {
	id: string;
	text: string;
	children?: TreeNode[];
}

// Text object for draft editing
export interface TextObject {
	id: string;
	text: string;
	indentValue: IndentValue;
}

// Content serialization type
export type ContentType = 'main' | 'sub';
export interface Content {
	type: ContentType;
	content: Array<Content | string>;
}

/**
 * Determine if a text object is "Main"
 */
export function isMainContent(obj: TextObject): boolean {
	return obj.indentValue === 'Main';
}

/**
 * Convert TextObject array to serialized nested array
 */
export function serializeContent(content: TextObject[]): Array<Array<string | string[]>> {
	const result: Array<Array<string | string[]>> = [];

	let current: Array<string | string[]> | null = null;
	let bullets: Array<string | string[]> = [];
	let subBullets: string[] = [];

	function flushBullets() {
		if (subBullets.length) {
			bullets.push(subBullets);
			subBullets = [];
		}
		if (bullets.length && current) {
			current.push(bullets);
			bullets = [];
		}
	}

	for (const obj of content) {
		if (isMainContent(obj)) {
			// finish previous main
			if (current) {
				flushBullets();
				result.push(current);
			}
			current = [obj.text];
			continue;
		}

		// bullets and sub-bullets
		if (obj.indentValue === 'Bullet') {
			if (subBullets.length) {
				bullets.push(subBullets);
				subBullets = [];
			}
			bullets.push(obj.text);
		} else if (obj.indentValue === 'Sub-Bullet') {
			subBullets.push(obj.text);
		}
	}

	if (current) flushBullets() && result.push(current);

	return result;
}
