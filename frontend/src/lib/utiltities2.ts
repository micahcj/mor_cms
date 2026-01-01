// utilities.ts
import type { TreeNode } from './static_resources';

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
