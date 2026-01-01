// utilities.ts
import type { TreeNode } from './static_resources';
import type { IndentValue, TextObject } from './static_resources2';
import { escapeHtml } from './utilities';

export interface TreeMutation {
	tree: TreeNode[];
}

/**
 * Recursively find a node by ID.
 */
export function findNode(
	nodes: TreeNode[],
	id: string,
	parent: TreeNode | null = null
): { node: TreeNode; parent: TreeNode | null; index: number } | null {
	for (let i = 0; i < nodes.length; i++) {
		const node = nodes[i];
		if (node.id === id) return { node, parent, index: i };

		if (node.children?.length) {
			const found = findNode(node.children, id, node);
			if (found) return found;
		}
	}
	return null;
}

/**
 * Move node before/after another node
 */
export function moveNodeById(
	nodes: TreeNode[],
	fromId: string,
	toId: string,
	position: 'before' | 'after'
): TreeMutation | null {
	if (fromId === toId) return null;

	const copy = structuredClone(nodes);
	const from = findNode(copy, fromId);
	const to = findNode(copy, toId);
	if (!from || !to) return null;

	const fromContainer = from.parent?.children ?? copy;
	const [removed] = fromContainer.splice(from.index, 1);

	const toContainer = to.parent?.children ?? copy;
	const insertIndex = position === 'before' ? to.index : to.index + 1;

	toContainer.splice(insertIndex, 0, removed);
	return { tree: copy };
}

/**
 * Indent node: make it a child of previous sibling
 */
export function indentNode(nodes: TreeNode[], id: string): TreeMutation | null {
	const copy = structuredClone(nodes);
	const found = findNode(copy, id);
	if (!found) return null;

	const container = found.parent?.children ?? copy;
	if (found.index === 0) return null; // cannot indent first item

	const newParent = container[found.index - 1];
	newParent.children ??= [];
	const [removed] = container.splice(found.index, 1);
	newParent.children.push(removed);

	return { tree: copy };
}

/**
 * Outdent node: move it out of its parent
 */
export function outdentNode(nodes: TreeNode[], id: string): TreeMutation | null {
	const copy = structuredClone(nodes);
	const found = findNode(copy, id);
	if (!found || !found.parent) return null;

	const parent = found.parent;
	const grand = findNode(copy, parent.id);
	if (!grand) return null;

	const parentContainer = grand.parent?.children ?? copy;
	parent.children!.splice(found.index, 1);
	parentContainer.splice(grand.index + 1, 0, found.node);

	return { tree: copy };
}

/**
 * Can the node be indented?
 */
export function canIndent(nodes: TreeNode[], id: string): boolean {
	const found = findNode(nodes, id);
	if (!found) return false;

	const container = found.parent?.children ?? nodes;
	return found.index > 0; // can indent if not first child
}

/**
 * Can the node be outdented?
 */
export function canOutdent(nodes: TreeNode[], id: string): boolean {
	const found = findNode(nodes, id);
	if (!found) return false;
	return !!found.parent;
}

// Add this to your utilities2.ts file

/**
 * Move a node before or after another node (reordering)
 */
export function reorderNode(
	nodes: TreeNode[],
	fromId: string,
	toId: string,
	position: 'before' | 'after'
): TreeMutation | null {
	if (fromId === toId) return null;

	const copy = structuredClone(nodes);
	const from = findNode(copy, fromId);
	const to = findNode(copy, toId);

	if (!from || !to) return null;

	// Can't move a parent into its own child
	if (isAncestor(from.node, to.node)) return null;

	// Remove from current location
	const fromContainer = from.parent?.children ?? copy;
	const [removed] = fromContainer.splice(from.index, 1);

	// Find the target again after removal (indices may have shifted)
	const toAfterRemoval = findNode(copy, toId);
	if (!toAfterRemoval) return null;

	// Insert at new location
	const toContainer = toAfterRemoval.parent?.children ?? copy;
	const insertIndex = position === 'before' ? toAfterRemoval.index : toAfterRemoval.index + 1;

	toContainer.splice(insertIndex, 0, removed);

	return { tree: copy };
}

/**
 * Check if a node is an ancestor of another node
 */
function isAncestor(potentialAncestor: TreeNode, node: TreeNode): boolean {
	if (!potentialAncestor.children) return false;

	for (const child of potentialAncestor.children) {
		if (child.id === node.id) return true;
		if (isAncestor(child, node)) return true;
	}

	return false;
}

// Add this to your static_resources2.ts or utilities2.ts

/**
 * Convert flat TextObject array to hierarchical TreeNode array
 */
export function textObjectsToTree(textObjs: TextObject[]): TreeNode[] {
	const root: TreeNode[] = [];
	const stack: { node: TreeNode; level: number }[] = [];

	for (const obj of textObjs) {
		const node: TreeNode = {
			id: obj.id,
			text: obj.text,
			children: []
		};

		// Determine level: Main=0, Bullet=1, Sub-Bullet=2
		const level = obj.indentValue === 'Main' ? 0 : obj.indentValue === 'Bullet' ? 1 : 2;

		// Pop stack until we find the parent level
		while (stack.length > 0 && stack[stack.length - 1].level >= level) {
			stack.pop();
		}

		if (level === 0) {
			// Main level - add to root
			root.push(node);
		} else if (stack.length > 0) {
			// Child level - add to parent
			const parent = stack[stack.length - 1].node;
			parent.children = parent.children || [];
			parent.children.push(node);
		}

		stack.push({ node, level });
	}

	return root;
}

/**
 * Convert hierarchical TreeNode array back to flat TextObject array
 */
export function treeToTextObjects(nodes: TreeNode[], level: number = 0): TextObject[] {
	const result: TextObject[] = [];

	const indentValue: IndentValue = level === 0 ? 'Main' : level === 1 ? 'Bullet' : 'Sub-Bullet';

	for (const node of nodes) {
		result.push({
			id: node.id,
			text: node.text,
			indentValue
		});

		if (node.children?.length) {
			result.push(...treeToTextObjects(node.children, level + 1));
		}
	}

	return result;
}

export function exportListHtml(nodes: TreeNode[], pretty: boolean = true): string {
	function render(list: TreeNode[], depth: number = 0): string {
		const indent = pretty ? '  '.repeat(depth) : '';
		const newline = pretty ? '\n' : '';

		let html = `${indent}<ul>${newline}`;

		for (const node of list) {
			html += `${indent}  <li>${escapeHtml(node.text)}`;

			if (node.children?.length) {
				html += `${newline}${render(node.children, depth + 2)}${indent}  `;
			}

			html += `</li>${newline}`;
		}

		html += `${indent}</ul>${newline}`;
		return html;
	}

	return render(nodes, 0);
}

/**
 * Export with CSS classes for styling based on depth
 */
export function exportListHtmlWithClasses(nodes: TreeNode[]): string {
	function render(list: TreeNode[], depth: number = 0): string {
		const indent = '  '.repeat(depth);
		const depthClass = `depth-${depth}`;

		let html = `${indent}<ul class="${depthClass}">\n`;

		for (const node of list) {
			html += `${indent}  <li class="node-item">${escapeHtml(node.text)}`;

			if (node.children?.length) {
				html += `\n${render(node.children, depth + 1)}${indent}  `;
			}

			html += `</li>\n`;
		}

		html += `${indent}</ul>\n`;
		return html;
	}

	return render(nodes, 0);
}

/**
 * Export to markdown format
 */
export function exportListMarkdown(nodes: TreeNode[]): string {
	function render(list: TreeNode[], depth: number = 0): string {
		const indent = '  '.repeat(depth);
		let md = '';

		for (const node of list) {
			md += `${indent}- ${node.text}\n`;

			if (node.children?.length) {
				md += render(node.children, depth + 1);
			}
		}

		return md;
	}

	return render(nodes, 0);
}
